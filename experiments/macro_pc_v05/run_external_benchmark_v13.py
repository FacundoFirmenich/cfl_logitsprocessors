#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import numpy as np
import torch
import transformers
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessorList, set_seed

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_macro_pc_gate_v05 as base
import run_macro_pc_gate_v07 as v7

PREREG_PATH = HERE / "PREREG_EXTERNAL_BENCHMARK_v1.3.json"
SYSTEM_P = v7.SYSTEM_P_BASE
SYSTEM_C = v7.SYSTEM_C

def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical(obj:Any)->str:
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def digest(obj:Any)->str:
    raw=obj if isinstance(obj,(bytes,bytearray)) else canonical(obj).encode()
    return hashlib.sha256(raw).hexdigest()

def format_prompt(tokenizer,prompt,system_prompt):
    msgs=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}]
    try:
        return tokenizer.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True),"SYSTEM_USER_NATIVE"
    except Exception:
        msgs=[{"role":"user","content":"SYSTEM INSTRUCTION:\n"+system_prompt+"\n\nUSER PROBLEM:\n"+prompt}]
        return tokenizer.apply_chat_template(msgs,tokenize=False,add_generation_prompt=True),"USER_COMBINED_FALLBACK"

def generate(model,tokenizer,*,prompt,system_prompt,seed,processor=None,max_new_tokens=128):
    set_seed(seed)
    formatted,template_mode=format_prompt(tokenizer,prompt,system_prompt)
    inputs=tokenizer(formatted,return_tensors="pt")
    kw={
        "max_new_tokens":max_new_tokens,
        "do_sample":True,
        "temperature":0.8,
        "top_p":0.9,
        "pad_token_id":tokenizer.pad_token_id,
        "eos_token_id":tokenizer.eos_token_id,
    }
    if processor is not None:
        kw["logits_processor"]=LogitsProcessorList([processor])
    with torch.inference_mode():
        out=model.generate(**inputs,**kw)
    n=int(inputs["input_ids"].shape[-1])
    ids=[int(x) for x in out[0,n:].tolist()]
    text=tokenizer.decode(ids,skip_special_tokens=True)
    return {"seed":seed,"text":text,"token_ids":ids,"template_mode":template_mode,
            "output_sha256":digest({"seed":seed,"text":text,"token_ids":ids})}

def l3_raw_prompt(problem,l1,l2):
    return (
        "ORIGINAL PROBLEM:\n"+problem+"\n\n"
        "PROCEDURAL ATTEMPT L1:\n"+l1+"\n\n"
        "PROCEDURAL ATTEMPT L2:\n"+l2+"\n\n"
        "THIRD-STAGE RAW SUBPHASE. Solve the ORIGINAL PROBLEM anew. "
        "Return only the requested answer and required FINAL field. "
        "Do not discuss L1, L2, stages, or orchestration."
    )

def l3_informed_prompt(problem,l1,l2,l3raw):
    return (
        "ORIGINAL PROBLEM:\n"+problem+"\n\n"
        "PROCEDURAL ATTEMPT L1:\n"+l1+"\n\n"
        "PROCEDURAL ATTEMPT L2:\n"+l2+"\n\n"
        "THIRD-STAGE RAW RESOLUTION:\n"+l3raw+"\n\n"
        "THIRD-STAGE INFORMED SUBPHASE. Produce the final answer after checking the prior resolutions. "
        "Return only the answer to the ORIGINAL PROBLEM and end with its required FINAL field. "
        "Do not mention prior attempts or orchestration."
    )

def parse_final_number(text:str):
    hits=re.findall(r"(?im)^\s*FINAL\s*:\s*([-+]?\d[\d,]*(?:\.\d+)?)\s*$",text)
    if not hits:return None
    try:return Decimal(hits[-1].replace(",",""))
    except InvalidOperation:return None

def parse_final_label(text:str,allowed:list[str]):
    hits=re.findall(r"(?im)^\s*FINAL\s*:\s*([A-Za-z0-9]+)\s*$",text)
    if not hits:return None
    x=hits[-1].strip()
    amap={str(a).upper():str(a) for a in allowed}
    return amap.get(x.upper())

def structural_vector(task:str,text:str,labels=None):
    if task=="gsm8k":
        parsed=parse_final_number(text)
        return {"parseable":int(parsed is not None),"contract":int(parsed is not None)}
    parsed=parse_final_label(text,labels or [])
    return {"parseable":int(parsed is not None),"contract":int(parsed is not None)}

def dominates(a,b):
    keys=["parseable","contract"]
    return all(a[k]>=b[k] for k in keys) and any(a[k]>b[k] for k in keys)

def structural_A_P(vectors):
    l3=vectors["L3_informed"]
    dominators=[s for s in ["L1","L2","L3_raw"] if dominates(vectors[s],l3)]
    frontier=[s for s,v in vectors.items() if not any(o!=s and dominates(ov,v) for o,ov in vectors.items())]
    if not dominators:
        return {"decision":"SELECT","selected_stage":"L3_informed","frontier":frontier,
                "gold_used":False,"reason":"L3_informed structurally nondominated."}
    if len(frontier)==1:
        return {"decision":"SELECT","selected_stage":frontier[0],"frontier":frontier,
                "gold_used":False,"reason":"Unique structural Pareto frontier stage."}
    return {"decision":"ABSTAIN","selected_stage":None,"frontier":frontier,
            "gold_used":False,"reason":"Multiple structurally incomparable frontier stages."}

def make_gsm_prompt(question):
    return (
        "Solve the following grade-school mathematics problem. You may show concise reasoning. "
        "Your last line must be exactly 'FINAL: <number>' with no units or commentary after it.\n\n"
        + question
    )

def make_arc_prompt(question,labels,texts):
    lines=[f"{l}. {t}" for l,t in zip(labels,texts)]
    return (
        "Choose the single best answer to the multiple-choice question. You may reason concisely. "
        "Your last line must be exactly 'FINAL: <label>' using one of the presented labels.\n\n"
        + question + "\n\n" + "\n".join(lines)
    )

def gsm_gold(answer):
    m=re.search(r"####\s*([-+]?\d[\d,]*(?:\.\d+)?)",answer)
    if not m:raise ValueError("GSM8K gold parse failed")
    return Decimal(m.group(1).replace(",",""))

def evaluate(task,text,gold,labels=None):
    if task=="gsm8k":
        pred=parse_final_number(text)
        return {"parseable":pred is not None,"prediction":str(pred) if pred is not None else None,
                "gold":str(gold),"correct":bool(pred is not None and pred==gold)}
    pred=parse_final_label(text,labels or [])
    return {"parseable":pred is not None,"prediction":pred,"gold":gold,
            "correct":bool(pred is not None and str(pred).upper()==str(gold).upper())}

def wtl(c,b):
    if c and not b:return "WIN"
    if b and not c:return "LOSS"
    return "TIE"

def posterior(counts,draws,rng):
    a=np.array([1+counts["WIN"],1+counts["TIE"],1+counts["LOSS"]],float)
    samp=rng.dirichlet(a,size=draws)
    mean=a/a.sum()
    return {
        "alpha":{"WIN":float(a[0]),"TIE":float(a[1]),"LOSS":float(a[2])},
        "mean":{"WIN":float(mean[0]),"TIE":float(mean[1]),"LOSS":float(mean[2])},
        "Pr_WIN_gt_LOSS":float(np.mean(samp[:,0]>samp[:,2]))
    }

def main():
    prereg=json.loads(PREREG_PATH.read_text())
    prereg_sha=hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    out=Path("external_v13_artifact");out.mkdir(parents=True,exist_ok=True)

    # Load external data; freeze exact selected contents into the artifact before model generation.
    gsm=load_dataset("openai/gsm8k","main",split="test")
    arc=load_dataset("allenai/ai2_arc","ARC-Challenge",split="test")

    items=[]
    for spec in prereg["datasets"]:
        ds=gsm if spec["name"]=="openai/gsm8k" else arc
        for idx in spec["indices"]:
            row=dict(ds[int(idx)])
            if spec["name"]=="openai/gsm8k":
                item={"dataset":"gsm8k","index":int(idx),"task":"gsm8k","question":row["question"],
                      "gold":str(gsm_gold(row["answer"])),"raw_answer":row["answer"]}
            else:
                labels=[str(x) for x in row["choices"]["label"]]
                texts=[str(x) for x in row["choices"]["text"]]
                item={"dataset":"arc_challenge","index":int(idx),"task":"arc","question":row["question"],
                      "labels":labels,"choice_texts":texts,"gold":str(row["answerKey"])}
            item["item_sha256"]=digest(item)
            items.append(item)
    selected={"schema":"external-selected-items/v1.3","created_at":utcnow(),"items":items}
    selected["sha256"]=digest(selected)
    (out/"selected_items.json").write_text(json.dumps(selected,indent=2,ensure_ascii=False),encoding="utf-8")

    model_id=prereg["model"]
    tok=AutoTokenizer.from_pretrained(model_id)
    if tok.pad_token_id is None:tok.pad_token_id=tok.eos_token_id
    model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    model.eval();torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))

    records=[]
    for item in items:
        task=item["task"]
        prompt=make_gsm_prompt(item["question"]) if task=="gsm8k" else make_arc_prompt(item["question"],item["labels"],item["choice_texts"])
        budget=prereg["generation"]["gsm8k_max_new_tokens"] if task=="gsm8k" else prereg["generation"]["arc_max_new_tokens"]
        for seed in prereg["replicate_seeds"]:
            seed=int(seed)
            # Candidate production sees no gold.
            l1=generate(model,tok,prompt=prompt,system_prompt=SYSTEM_P,seed=seed,max_new_tokens=budget)
            l2=generate(model,tok,prompt=prompt,system_prompt=SYSTEM_P,seed=seed+1000,max_new_tokens=budget)
            l3r=generate(model,tok,prompt=l3_raw_prompt(prompt,l1["text"],l2["text"]),
                         system_prompt="Third procedural stage, raw subphase. Solve the original task and preserve its FINAL contract.",
                         seed=seed+2000,max_new_tokens=budget)
            l3i=generate(model,tok,prompt=l3_informed_prompt(prompt,l1["text"],l2["text"],l3r["text"]),
                         system_prompt="Third procedural stage, informed subphase. Return the final task answer with the required FINAL field.",
                         seed=seed+3000,max_new_tokens=budget)
            stages={"L1":l1,"L2":l2,"L3_raw":l3r,"L3_informed":l3i}
            vectors={s:structural_vector(task,r["text"],item.get("labels")) for s,r in stages.items()}
            ap=structural_A_P(vectors)
            if ap["decision"]=="SELECT":
                ps=ap["selected_stage"];ptext=stages[ps]["text"];pavail=True
            else:
                ps=None;ptext=None;pavail=False

            proc=base.TALMMassRightSoftProcessor(base.TALMMassRightSoftConfig())
            c=generate(model,tok,prompt=prompt,system_prompt=SYSTEM_C,seed=seed,processor=proc,max_new_tokens=budget)

            # Freeze all candidates + BASELINE macro decision before gold evaluation.
            freeze={
                "dataset":item["dataset"],"index":item["index"],"seed":seed,
                "item_sha256":item["item_sha256"],
                "baseline_sha256":l1["output_sha256"],
                "P_available":pavail,"P_stage":ps,
                "P_sha256":digest({"text":ptext}) if ptext is not None else None,
                "C_sha256":c["output_sha256"],
                "macro_decision":"BASELINE",
                "gold_visible_to_generation":False,
                "gold_visible_to_A_P":False,
            }
            freeze["freeze_sha256"]=digest(freeze)

            # Gold evaluation happens only here.
            gold=Decimal(item["gold"]) if task=="gsm8k" else item["gold"]
            be=evaluate(task,l1["text"],gold,item.get("labels"))
            pe=evaluate(task,ptext,gold,item.get("labels")) if pavail else None
            ce=evaluate(task,c["text"],gold,item.get("labels"))

            rec={
                "schema":"cfl-external-heldout-record/v1.3","created_at":utcnow(),
                "dataset":item["dataset"],"index":item["index"],"item_sha256":item["item_sha256"],
                "seed":seed,"task":task,"candidate_freeze":freeze,
                "P":{"available":pavail,"selected_stage":ps,"A_P":ap,"structural_vectors":vectors,
                     "evaluation":pe},
                "C":{"evaluation":ce,"diagnostics":proc.diagnostics},
                "baseline":{"evaluation":be},
                "WTL":{
                    "P":wtl(bool(pe["correct"]),bool(be["correct"])) if pavail else "NO_DECISION",
                    "C":wtl(bool(ce["correct"]),bool(be["correct"]))
                }
            }
            rec["sha256"]=digest(rec)
            records.append(rec)

    (out/"records.json").write_text(json.dumps(records,indent=2,ensure_ascii=False),encoding="utf-8")

    rng=np.random.default_rng(int(prereg["outcome"]["rng_seed"]))
    summaries={}
    for proc in ["P","C"]:
        usable=[r for r in records if r["WTL"][proc]!="NO_DECISION"]
        cnt={k:sum(r["WTL"][proc]==k for r in usable) for k in ["WIN","TIE","LOSS"]}
        dsets={}
        for ds in sorted(set(r["dataset"] for r in usable)):
            rr=[r for r in usable if r["dataset"]==ds]
            dc={k:sum(x["WTL"][proc]==k for x in rr) for k in ["WIN","TIE","LOSS"]}
            dsets[ds]={"n":len(rr),"counts":dc}
        post=posterior(cnt,int(prereg["outcome"]["mc_draws"]),rng)
        support=len(usable)>=prereg["gates"]["support"]["min_pairs"] and len(dsets)>=prereg["gates"]["support"]["min_datasets"]
        util=post["Pr_WIN_gt_LOSS"]>=0.95
        transp=(len(dsets)>=2 and all(v["n"]>=6 and v["counts"]["LOSS"]<=v["counts"]["WIN"] for v in dsets.values()))
        accuracy={
            "baseline":sum(r["baseline"]["evaluation"]["correct"] for r in usable)/len(usable) if usable else None,
            proc:sum(r[proc]["evaluation"]["correct"] for r in usable)/len(usable) if usable else None,
        }
        summaries[proc]={
            "n":len(usable),"counts":cnt,"datasets":dsets,"posterior":post,"accuracy":accuracy,
            "gates":{"support":support,"utility_risk":util,"dataset_transportability":transp},
            "provisional_external_evidence":bool(support and util and transp),
            "operational_authority":False
        }

    summary={
        "schema":"cfl-external-benchmark-summary/v1.3","created_at":utcnow(),
        "prereg_sha256":prereg_sha,"selected_items_sha256":selected["sha256"],
        "model_id":model_id,"n_records":len(records),"process_summaries":summaries,
        "authority_transfer":False,"global_macro_prior_changed":False,
        "claim_boundary":prereg["claim_boundary"]
    }
    summary["sha256"]=digest(summary)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")

    head="0"*64;events=[]
    for r in records:
        ev={"index":len(events),"event_type":"EXTERNAL_OUTCOME_RECORDED","created_at":utcnow(),
            "payload":{"dataset":r["dataset"],"index":r["index"],"seed":r["seed"],"freeze_sha256":r["candidate_freeze"]["freeze_sha256"],"WTL":r["WTL"]},"prev_hash":head}
        ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    ev={"index":len(events),"event_type":"EXTERNAL_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"process_summaries":summaries},"prev_hash":head}
    ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    with (out/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:f.write(canonical(ev)+"\n")

    manifest={
        "schema":"cfl-external-benchmark-gate/v1.3","created_at":utcnow(),"status":"PASS_EXECUTION",
        "prereg_sha256":prereg_sha,"selected_items_sha256":selected["sha256"],
        "real_model_execution":True,"real_TALM_execution":True,"synthetic_observations":False,
        "gold_leakage_to_generation":False,"gold_leakage_to_A_P":False,
        "authority_transfer":False,"global_macro_prior_changed":False,
        "summary_sha256":summary["sha256"],"ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(out.glob("*")):
        if p.is_file() and p.name!="manifest.json":
            manifest.setdefault("files",{})[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

    print(json.dumps({"summary":summary,"ledger_head_hash":head},indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
