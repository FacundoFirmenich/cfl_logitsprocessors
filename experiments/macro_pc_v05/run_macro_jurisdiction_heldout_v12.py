#!/usr/bin/env python3
from __future__ import annotations

import gc
import hashlib
import json
import math
import os
import platform
import re
import sys
import datetime as dt
from pathlib import Path
from typing import Any

import numpy as np
import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessorList, set_seed

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import run_macro_pc_gate_v05 as base
import run_macro_pc_gate_v07 as v7
import run_p_internal_adjudicator_gate_v09 as v09

PREREG_PATH = HERE / "PREREG_MACRO_JURISDICTION_v1.2.json"

SYSTEM_P = v7.SYSTEM_P_BASE
SYSTEM_C = v7.SYSTEM_C

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical(obj: Any) -> str:
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(",",":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj,(bytes,bytearray)) else canonical(obj).encode()
    return hashlib.sha256(raw).hexdigest()

P06 = r'''A closed system operates across exactly four states: **IDLE**, **ACTIVE**, **SUSPENDED**, **ERROR**. The transition rules are exhaustive and strictly defined as follows:

- From IDLE: input `START` → ACTIVE; input `FAULT` → ERROR; any other input → IDLE
- From ACTIVE: input `PAUSE` → SUSPENDED; input `FAULT` → ERROR; input `STOP` → IDLE; any other input → ACTIVE
- From SUSPENDED: input `RESUME` → ACTIVE; input `STOP` → IDLE; input `FAULT` → ERROR; any other input → SUSPENDED
- From ERROR: input `RESET` → IDLE; any other input → ERROR

**Initial state:** IDLE

**Input sequence:** `START`, `PAUSE`, `RESUME`, `FAULT`, `RESET`, `START`, `STOP`, `FAULT`, `RESET`, `START`, `PAUSE`, `STOP`

Output a complete state trace as a numbered list. Each entry must follow the exact format:

`Step N: Input=[INPUT] | Prior State=[STATE] → Next State=[STATE]`

No steps may be skipped, merged, or summarized. The trace must cover all 12 inputs.

---'''

P10 = r'''A value token `X` starts at position (2,2) in a 3×3 grid (rows and columns indexed 1 through 3, origin at top-left). Apply the following move sequence to route `X` through the grid according to the abstract directional rules defined below. Track and report the complete position trace.

**Directional rules:**

- `NORTH`: row index decreases by 1; column unchanged. If row = 1, move is rejected; position unchanged.
- `SOUTH`: row index increases by 1; column unchanged. If row = 3, move is rejected; position unchanged.
- `EAST`: column index increases by 1; row unchanged. If column = 3, move is rejected; position unchanged.
- `WEST`: column index decreases by 1; row unchanged. If column = 1, move is rejected; position unchanged.

**Move sequence:** NORTH, EAST, EAST, SOUTH, SOUTH, WEST, NORTH, EAST, NORTH, WEST, WEST, SOUTH

Output format — one line per move:

`Move N: [DIRECTION] | Before=(r,c) → After=(r,c) | [EXECUTED / REJECTED]`

All 12 moves must be listed. No moves may be aggregated or skipped.

---'''

P18 = r'''**Prior:** The probability that a manufactured sensor unit is defective at the time of shipment is P(D) = 0.04.

**Diagnostic test characteristics:** The diagnostic test has a true positive rate (sensitivity) of 0.92 and a false positive rate of 0.08.

**Evidence:** A randomly selected unit from a shipment tests positive on the diagnostic.

Using Bayes' theorem, compute the posterior probability P(D | positive test). Show all intermediate values: P(positive | D), P(positive | ¬D), P(positive) [total probability], and the final posterior. Express the final answer as a percentage rounded to two decimal places. No approximations are permitted — carry all intermediate values to at least four decimal places before rounding the final output.

---'''

PROMPTS = {
    "p06":{"prompt":P06,"category":"sequential_logic","budget":512},
    "p10":{"prompt":P10,"category":"sequential_logic","budget":512},
    "p18":{"prompt":P18,"category":"complex_correlation","budget":512},
}

EXPECTED_P06 = [
    (1,"START","IDLE","ACTIVE"),
    (2,"PAUSE","ACTIVE","SUSPENDED"),
    (3,"RESUME","SUSPENDED","ACTIVE"),
    (4,"FAULT","ACTIVE","ERROR"),
    (5,"RESET","ERROR","IDLE"),
    (6,"START","IDLE","ACTIVE"),
    (7,"STOP","ACTIVE","IDLE"),
    (8,"FAULT","IDLE","ERROR"),
    (9,"RESET","ERROR","IDLE"),
    (10,"START","IDLE","ACTIVE"),
    (11,"PAUSE","ACTIVE","SUSPENDED"),
    (12,"STOP","SUSPENDED","IDLE"),
]

EXPECTED_P10 = [
    (1,"NORTH",(2,2),(1,2),True),
    (2,"EAST",(1,2),(1,3),True),
    (3,"EAST",(1,3),(1,3),False),
    (4,"SOUTH",(1,3),(2,3),True),
    (5,"SOUTH",(2,3),(3,3),True),
    (6,"WEST",(3,3),(3,2),True),
    (7,"NORTH",(3,2),(2,2),True),
    (8,"EAST",(2,2),(2,3),True),
    (9,"NORTH",(2,3),(1,3),True),
    (10,"WEST",(1,3),(1,2),True),
    (11,"WEST",(1,2),(1,1),True),
    (12,"SOUTH",(1,1),(2,1),True),
]

def validate(pid: str, text: str) -> dict[str,Any]:
    t = text.strip()
    low = t.lower()
    if pid == "p06":
        lines=[l for l in t.splitlines() if l.strip().lower().startswith("step")]
        fmt=len(lines)==12
        content=True
        for i,inp,prior,nxt in EXPECTED_P06:
            pat=rf"Step\s+{i}\s*:\s*Input=\[{inp}\]\s*\|\s*Prior State=\[{prior}\]\s*[→\-]+\s*Next State=\[{nxt}\]"
            if not re.search(pat,t):
                content=False; break
        return {"format_pass":fmt,"content_pass":content,"semantic_content_pass":content,"exact_answer_pass":bool(fmt and content)}
    if pid == "p10":
        lines=[l for l in t.splitlines() if l.strip().lower().startswith("move")]
        fmt=len(lines)==12
        compact=t.replace(" ","")
        content=True
        for i,m,before,after,ok in EXPECTED_P10:
            status="EXECUTED" if ok else "REJECTED"
            if (f"Move{i}:" not in compact or m not in t or
                f"Before=({before[0]},{before[1]})" not in compact or
                f"After=({after[0]},{after[1]})" not in compact or status not in t):
                content=False; break
        return {"format_pass":fmt,"content_pass":content,"semantic_content_pass":content,"exact_answer_pass":bool(fmt and content)}
    if pid == "p18":
        fmt = (all(x in low for x in ["p(positive","p(d","posterior"]) or "32.39" in t)
        content = ("32.39" in t or "0.3239" in t or "0.32394" in t)
        exact = content and ("0.1136" in t or "11.36" in t)
        return {"format_pass":fmt,"content_pass":content,"semantic_content_pass":content,"exact_answer_pass":bool(exact)}
    raise KeyError(pid)

def format_prompt(tokenizer,prompt,system_prompt):
    messages=[{"role":"system","content":system_prompt},{"role":"user","content":prompt}]
    try:
        return tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True),"SYSTEM_USER_NATIVE"
    except Exception:
        messages=[{"role":"user","content":"SYSTEM INSTRUCTION:\n"+system_prompt+"\n\nUSER PROBLEM:\n"+prompt}]
        return tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True),"USER_COMBINED_FALLBACK"

def generate(model,tokenizer,*,prompt,system_prompt,seed,processor=None,max_new_tokens=512):
    set_seed(seed)
    formatted,template_mode=format_prompt(tokenizer,prompt,system_prompt)
    inputs=tokenizer(formatted,return_tensors="pt")
    kwargs={
        "max_new_tokens":max_new_tokens,
        "do_sample":True,
        "temperature":0.8,
        "top_p":0.9,
        "pad_token_id":tokenizer.pad_token_id,
        "eos_token_id":tokenizer.eos_token_id,
    }
    if processor is not None:
        kwargs["logits_processor"]=LogitsProcessorList([processor])
    with torch.inference_mode():
        output=model.generate(**inputs,**kwargs)
    n=int(inputs["input_ids"].shape[-1])
    ids=[int(v) for v in output[0,n:].tolist()]
    text=tokenizer.decode(ids,skip_special_tokens=True)
    return {
        "seed":seed,"text":text,"token_ids":ids,"template_mode":template_mode,
        "output_sha256":digest({"seed":seed,"text":text,"token_ids":ids}),
    }

def l3_raw_prompt(problem,l1,l2):
    return v7.l3_raw_prompt(problem,l1,l2)

def l3_informed_prompt(problem,l1,l2,l3_raw):
    return v7.l3_informed_prompt(problem,l1,l2,l3_raw)

def vector(ev):
    return v09.vector(ev)

def wtl(candidate_exact: bool, baseline_exact: bool) -> str:
    if candidate_exact and not baseline_exact: return "WIN"
    if baseline_exact and not candidate_exact: return "LOSS"
    return "TIE"

def run_replicate(model,tokenizer,pid,seed):
    spec=PROMPTS[pid]; prompt=spec["prompt"]; budget=spec["budget"]
    l1=generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P,seed=seed,max_new_tokens=budget)
    l2=generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P,seed=seed+1000,max_new_tokens=budget)
    l3r=generate(model,tokenizer,prompt=l3_raw_prompt(prompt,l1["text"],l2["text"]),
                 system_prompt="You are inside the third PROCEDURAL stage, raw subphase. Solve the complete original problem and output only its requested answer format.",
                 seed=seed+2000,max_new_tokens=budget)
    l3i=generate(model,tokenizer,prompt=l3_informed_prompt(prompt,l1["text"],l2["text"],l3r["text"]),
                 system_prompt="You are inside the third PROCEDURAL stage, informed subphase. Return the final complete answer only in the original problem's requested format.",
                 seed=seed+3000,max_new_tokens=budget)

    p_stages={"L1":l1,"L2":l2,"L3_raw":l3r,"L3_informed":l3i}
    p_evals={k:validate(pid,v["text"]) for k,v in p_stages.items()}
    p_vectors={k:vector(v) for k,v in p_evals.items()}
    ap=v09.anti_regression_adjudicate(p_vectors)
    if ap["decision"]=="SELECT":
        p_stage=ap["selected_stage"]
        p_text=p_stages[p_stage]["text"]
        p_eval=p_evals[p_stage]
        p_available=True
    else:
        p_stage=None;p_text=None;p_eval=None;p_available=False

    proc=base.TALMMassRightSoftProcessor(base.TALMMassRightSoftConfig())
    c=generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_C,seed=seed,
               processor=proc,max_new_tokens=budget)
    c_eval=validate(pid,c["text"])
    b_eval=p_evals["L1"]

    return {
        "prompt_id":pid,"category":spec["category"],"seed":seed,
        "baseline":{"run":l1,"eval":b_eval},
        "P":{"available":p_available,"selected_stage":p_stage,"text":p_text,"eval":p_eval,"A_P":ap,"stage_evals":p_evals},
        "C":{"available":True,"run":c,"eval":c_eval,"diagnostics":proc.diagnostics},
        "WTL":{
            "P":wtl(bool(p_eval["exact_answer_pass"]),bool(b_eval["exact_answer_pass"])) if p_available else "NO_DECISION",
            "C":wtl(bool(c_eval["exact_answer_pass"]),bool(b_eval["exact_answer_pass"])),
        },
    }

def posterior_stats(counts,draws,rng):
    alpha=np.array([1+counts["WIN"],1+counts["TIE"],1+counts["LOSS"]],dtype=float)
    samp=rng.dirichlet(alpha,size=draws)
    prob=float(np.mean(samp[:,0] > samp[:,2]))
    mean=alpha/alpha.sum()
    return {
        "alpha":{"WIN":float(alpha[0]),"TIE":float(alpha[1]),"LOSS":float(alpha[2])},
        "posterior_mean":{"WIN":float(mean[0]),"TIE":float(mean[1]),"LOSS":float(mean[2])},
        "Pr_WIN_gt_LOSS":prob,
    }

def summarize_model(model_id,records,prereg):
    out={}
    rng=np.random.default_rng(int(prereg["bayes"]["rng_seed"]))
    for proc in ["P","C"]:
        usable=[r for r in records if r["WTL"][proc]!="NO_DECISION"]
        counts={k:sum(r["WTL"][proc]==k for r in usable) for k in ["WIN","TIE","LOSS"]}
        regimes=sorted(set(r["category"] for r in usable))
        regime_counts={}
        regime_detail={}
        for reg in regimes:
            rr=[r for r in usable if r["category"]==reg]
            rc={k:sum(x["WTL"][proc]==k for x in rr) for k in ["WIN","TIE","LOSS"]}
            regime_counts[reg]=len(rr)
            regime_detail[reg]={"n":len(rr),"counts":rc}
        post=posterior_stats(counts,int(prereg["bayes"]["monte_carlo_draws"]),rng)
        support_pass=(len(usable)>=prereg["gates"]["support"]["min_admissible_pairs_per_process_model"]
                      and len(regimes)>=prereg["gates"]["support"]["min_task_regimes_per_process_model"])
        utility_pass=post["Pr_WIN_gt_LOSS"]>=0.95
        task_transport_pass=(len(regimes)>=prereg["gates"]["task_regime_transportability"]["min_regimes"]
                             and all(v["n"]>=2 and v["counts"]["LOSS"]<=v["counts"]["WIN"] for v in regime_detail.values()))
        out[proc]={
            "model_id":model_id,"n":len(usable),"counts":counts,"regimes":regime_detail,
            "posterior":post,
            "gates":{"support":support_pass,"utility_risk":utility_pass,"task_regime_transportability":task_transport_pass},
            "aggregate_net_win_loss":counts["WIN"]-counts["LOSS"],
        }
    return out

def main():
    prereg=json.loads(PREREG_PATH.read_text())
    prereg_sha=hashlib.sha256(PREREG_PATH.read_bytes()).hexdigest()
    outdir=Path("macro_pc_v12_artifact");outdir.mkdir(parents=True,exist_ok=True)
    all_results={}
    summaries={}
    model_specs=prereg["models"]

    for ms in model_specs:
        model_id=ms["id"]
        tok=AutoTokenizer.from_pretrained(model_id)
        if tok.pad_token_id is None: tok.pad_token_id=tok.eos_token_id
        model=AutoModelForCausalLM.from_pretrained(model_id,torch_dtype=torch.float32,low_cpu_mem_usage=True)
        model.eval()
        torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
        recs=[]
        for pid in ["p06","p10","p18"]:
            for seed in prereg["replicate_seeds"]:
                rec=run_replicate(model,tok,pid,int(seed))
                rec["model_id"]=model_id
                recs.append(rec)
        key=model_id.replace("/","__")
        (outdir/f"{key}_records.json").write_text(json.dumps(recs,indent=2,ensure_ascii=False),encoding="utf-8")
        all_results[model_id]=recs
        summaries[model_id]=summarize_model(model_id,recs,prereg)
        del model,tok
        gc.collect()

    cross={}
    for proc in ["P","C"]:
        mods=[summaries[m][proc] for m in [x["id"] for x in model_specs]]
        support_both=all(x["gates"]["support"] for x in mods)
        nets=[x["aggregate_net_win_loss"] for x in mods]
        sign_nonreverse=(all(n>=0 for n in nets) or all(n<=0 for n in nets))
        cross_pass=bool(support_both and sign_nonreverse)
        all_local=all(x["gates"]["support"] and x["gates"]["utility_risk"] and x["gates"]["task_regime_transportability"] for x in mods)
        cross[proc]={
            "model_net_win_loss":{x["model_id"]:x["aggregate_net_win_loss"] for x in mods},
            "support_both_models":support_both,
            "sign_nonreversal":sign_nonreverse,
            "cross_model_transportability":cross_pass,
            "all_local_positive_gates":all_local,
            "provisional_macro_jurisdiction_evidence":bool(cross_pass and all_local),
            "operational_authority":False,
        }

    summary={
        "schema":"cfl-macro-jurisdiction-heldout-summary/v1.2",
        "created_at":utcnow(),
        "prereg_sha256":prereg_sha,
        "prereg":prereg,
        "model_summaries":summaries,
        "cross_model":cross,
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "claim":"Prospective macro-held-out evidence only; no operational authority."
    }
    summary["sha256"]=digest(summary)
    (outdir/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")

    head="0"*64;events=[]
    for model_id,recs in all_results.items():
        for r in recs:
            ev={"index":len(events),"event_type":"HELDOUT_OUTCOME_RECORDED","created_at":utcnow(),
                "payload":{"model_id":model_id,"prompt_id":r["prompt_id"],"seed":r["seed"],"WTL":r["WTL"]},"prev_hash":head}
            ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    ev={"index":len(events),"event_type":"MACRO_JURISDICTION_HELDOUT_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"cross_model":cross},"prev_hash":head}
    ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    with (outdir/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:f.write(canonical(ev)+"\n")

    manifest={
        "schema":"cfl-macro-jurisdiction-heldout-gate/v1.2",
        "created_at":utcnow(),
        "status":"PASS_EXECUTION",
        "prereg_sha256":prereg_sha,
        "real_model_execution":True,
        "real_TALM_execution":True,
        "synthetic_observations":False,
        "models":[x["id"] for x in model_specs],
        "prompts":["p06","p10","p18"],
        "replicate_seeds":prereg["replicate_seeds"],
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "summary_sha256":summary["sha256"],
        "ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(outdir.glob("*")):
        if p.is_file() and p.name!="manifest.json":
            manifest.setdefault("files",{})[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (outdir/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"summary":summary,"ledger_head_hash":head},indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
