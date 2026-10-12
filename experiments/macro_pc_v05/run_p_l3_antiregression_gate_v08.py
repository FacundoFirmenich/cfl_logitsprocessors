#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_macro_pc_gate_v05 as base
import run_macro_pc_gate_v07 as v7

MODEL_ID = v7.MODEL_ID
SOURCE_NOTEBOOK = v7.SOURCE_NOTEBOOK
PROMPTS = v7.PROMPTS
VALIDATORS = v7.VALIDATORS
SYSTEM_P_BASE = v7.SYSTEM_P_BASE
SEEDS = v7.SEEDS

STAGES = ["L1","L2","L3_raw","L3_informed"]

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def stage_vector(ev: dict[str,Any]) -> dict[str,int]:
    semantic = bool(ev.get("semantic_content_pass", ev.get("content_pass", False)))
    return {
        "semantic": int(semantic),
        "format": int(bool(ev.get("format_pass", False))),
        "exact": int(bool(ev.get("exact_answer_pass", False))),
    }

def dominates(a: dict[str,int], b: dict[str,int]) -> bool:
    keys = ["semantic","format","exact"]
    return all(a[k] >= b[k] for k in keys) and any(a[k] > b[k] for k in keys)

def relation_to_prior(stage_vec: dict[str,int], prior_vecs: dict[str,dict[str,int]]) -> dict[str,Any]:
    dominators = [name for name,v in prior_vecs.items() if dominates(v, stage_vec)]
    dominates_prior = [name for name,v in prior_vecs.items() if dominates(stage_vec, v)]
    prior_exact_pass = [name for name,v in prior_vecs.items() if v["exact"] == 1]
    lost_exact = bool(prior_exact_pass and stage_vec["exact"] == 0)
    if lost_exact or dominators:
        status = "REGRESSION"
    elif dominates_prior:
        status = "IMPROVEMENT"
    else:
        status = "NONDOMINATED_NEUTRAL"
    return {
        "status": status,
        "dominated_by_prior": dominators,
        "dominates_prior": dominates_prior,
        "prior_exact_pass_stages": prior_exact_pass,
        "lost_prior_exact_pass": lost_exact,
    }

def generate_case(model, tokenizer, pid: str) -> dict[str,Any]:
    spec=PROMPTS[pid]
    prompt=spec["prompt"]; budget=int(spec["budget"])
    l1=base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,seed=SEEDS["L1"],max_new_tokens=budget)
    l2=base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,seed=SEEDS["L2"],max_new_tokens=budget)
    l3_raw=base.generate(
        model,tokenizer,
        prompt=v7.l3_raw_prompt(prompt,l1["text"],l2["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, raw subphase. Solve the complete original problem and output only its requested answer format.",
        seed=SEEDS["L3_RAW"],max_new_tokens=budget
    )
    l3_informed=base.generate(
        model,tokenizer,
        prompt=v7.l3_informed_prompt(prompt,l1["text"],l2["text"],l3_raw["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, informed subphase. Return the final complete answer only in the original problem's requested format.",
        seed=SEEDS["L3_INFORMED"],max_new_tokens=budget
    )
    return {
        "prompt_id":pid,
        "regime":spec["regime"],
        "budget":budget,
        "stages":{"L1":l1,"L2":l2,"L3_raw":l3_raw,"L3_informed":l3_informed}
    }

def main() -> int:
    out=Path("macro_pc_v08_artifact"); out.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
    tok=AutoTokenizer.from_pretrained(MODEL_ID)
    if tok.pad_token_id is None: tok.pad_token_id=tok.eos_token_id
    model=AutoModelForCausalLM.from_pretrained(MODEL_ID,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    model.eval()

    cases={}
    regression_count=0
    improvement_count=0
    exact_preservation_count=0
    exact_opportunities=0

    for pid in ["p01","p03","p04"]:
        g=generate_case(model,tok,pid)
        validator=VALIDATORS[pid]
        evals={}
        vectors={}
        for stage in STAGES:
            txt=g["stages"][stage]["text"].strip()
            ev=validator(txt)
            evals[stage]=ev
            vectors[stage]=stage_vector(ev)

        prior={s:vectors[s] for s in ["L1","L2","L3_raw"]}
        relation=relation_to_prior(vectors["L3_informed"],prior)
        if relation["status"]=="REGRESSION": regression_count+=1
        if relation["status"]=="IMPROVEMENT": improvement_count+=1
        if relation["prior_exact_pass_stages"]:
            exact_opportunities += 1
            if vectors["L3_informed"]["exact"]==1: exact_preservation_count += 1

        record={
            "schema":"cfl-p-l3-antiregression-case/v0.8",
            "created_at":utcnow(),
            "prompt_id":pid,
            "regime":g["regime"],
            "source_budget":g["budget"],
            "seeds":SEEDS,
            "stages":g["stages"],
            "evaluations":evals,
            "vectors":vectors,
            "l3_informed_vs_prior":relation,
        }
        record["sha256"]=digest(record)
        cases[pid]=record
        (out/f"{pid}_antiregression.json").write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8")

    exact_preservation_rate = (
        exact_preservation_count/exact_opportunities if exact_opportunities else None
    )
    summary={
        "schema":"cfl-p-l3-antiregression-summary/v0.8",
        "created_at":utcnow(),
        "model_id":MODEL_ID,
        "source_notebook":SOURCE_NOTEBOOK,
        "cases":["p01","p03","p04"],
        "criterion":{
            "no_scalar_score":True,
            "regression":"a prior stage Pareto-dominates L3_informed on semantic/format/exact OR L3_informed loses a prior exact PASS",
            "improvement":"L3_informed Pareto-dominates at least one prior stage and is not dominated",
            "neutral":"otherwise nondominated",
        },
        "counts":{
            "regression_cases":regression_count,
            "improvement_cases":improvement_count,
            "neutral_cases":3-regression_count-improvement_count,
            "exact_preservation_opportunities":exact_opportunities,
            "exact_preserved":exact_preservation_count,
        },
        "exact_preservation_rate":exact_preservation_rate,
        "gate_pass": regression_count==0 and (
            exact_preservation_rate is None or exact_preservation_rate==1.0
        ),
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "case_status":{pid:cases[pid]["l3_informed_vs_prior"]["status"] for pid in cases},
    }
    summary["sha256"]=digest(summary)
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

    # Freeze a post-hoc diagnosis only. No authority posterior is updated here.
    zpost={
        "schema":"cfl-p-l3-antiregression-zpost/v0.8",
        "created_at":utcnow(),
        "cases":{
            pid:{
                "regime":cases[pid]["regime"],
                "vectors":cases[pid]["vectors"],
                "relation":cases[pid]["l3_informed_vs_prior"],
            } for pid in cases
        },
        "authority_transfer":False,
        "recommendation":(
            "PROMOTE_TWO_PHASE_L3_INTERFACE" if summary["gate_pass"]
            else "DO_NOT_PROMOTE_L3_INFORMED; add ex-ante anti-regression selection/fail-closed rule"
        ),
    }
    zpost["sha256"]=digest(zpost)
    (out/"z_post.json").write_text(json.dumps(zpost,indent=2),encoding="utf-8")

    head="0"*64; events=[]
    for pid in ["p01","p03","p04"]:
        ev={"index":len(events),"event_type":"CASE_ABLATION_FROZEN","created_at":utcnow(),
            "payload":{"prompt_id":pid,"case_sha256":cases[pid]["sha256"],"status":cases[pid]["l3_informed_vs_prior"]["status"]},
            "prev_hash":head}
        ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    ev={"index":len(events),"event_type":"ANTI_REGRESSION_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"gate_pass":summary["gate_pass"],"zpost_sha256":zpost["sha256"]},
        "prev_hash":head}
    ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    with (out/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events: f.write(canonical_json(ev)+"\n")

    manifest={
        "schema":"cfl-p-l3-antiregression-gate/v0.8",
        "created_at":utcnow(),
        "status":"PASS" if summary["gate_pass"] else "FAIL_WITH_EVIDENCE",
        "model_id":MODEL_ID,
        "real_model_execution":True,
        "synthetic_observations":False,
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "summary_sha256":summary["sha256"],
        "zpost_sha256":zpost["sha256"],
        "ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(out.glob("*")):
        if p.is_file() and p.name!="manifest.json":
            manifest.setdefault("files",{})[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps({"summary":summary,"zpost_recommendation":zpost["recommendation"],"ledger_head_hash":head},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
