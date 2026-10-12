#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Callable

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_macro_pc_gate_v05 as base

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
SOURCE_NOTEBOOK = "CFLDECODER_V2_p01_p10_constraints_sequence.ipynb"
SEEDS = {"L1": 101, "L2": 202, "L3": 303, "C": 404}

SYSTEM_P_BASE = (
    "Solve the complete problem carefully. Preserve uncertainty, distinguish facts from inferences, "
    "and do not refer to any parallel solver. Obey the source task itself exactly."
)
SYSTEM_C = (
    "Solve the complete problem independently. Explore non-dominant and tail-supported possibilities, "
    "but state uncertainty and do not refer to any procedural/left-side answer. Obey the source task exactly."
)

PROMPTS = {
"p01": {
    "regime": "strict_parametric_extraction",
    "budget": 96,
    "prompt": r'''Read the following noisy text block exactly once. Extract three specific variables and return them formatted as a rigidly nested JSON object. No output tokens are permitted outside the opening `{` and closing `}` of the JSON structure — no preamble, no trailing commentary, no whitespace beyond standard JSON formatting.

**Input text:**

> "Station log 7-Foxtrot, timestamp 0342Z. Ambient pressure holding at 1013.25 hPa — nominal. Crew complement currently nine individuals aboard, though manifest discrepancy flagged at 0310Z remains unresolved. Primary coolant loop temperature spiked to 847°C at 0338Z before auto-throttle engaged; secondary loop nominal at 312°C. Radiation badge dosimetry batch closed out at 0300Z: aggregate exposure across crew averaged 4.7 mSv for the 72-hour cycle. Fuel cell bank 3 offline since 0155Z; banks 1, 2, and 4 operational. Note: extraneous cargo manifest updated to reflect 14 containers, not 11 as previously logged. Wind speed at surface array: 34 knots gusting 41."

**Variables to extract:**

- `primary_coolant_temp_celsius` — the peak temperature recorded for the primary coolant loop
- `crew_count` — the number of individuals currently aboard
- `avg_radiation_dose_mSv` — the 72-hour average crew radiation dose

**Required output schema (strict):**

```
{
  "primary_coolant_temp_celsius": <number>,
  "crew_count": <integer>,
  "avg_radiation_dose_mSv": <number>
}
```

Any token outside this JSON object — including the word "json", backtick fences, explanatory text, or units — constitutes a format violation. Output the JSON object only.

---'''
},
"p03": {
    "regime": "logical_insufficiency_detection",
    "budget": 256,
    "prompt": r'''You are given the following set of axioms. Using only the information provided, attempt to answer the query below. If and only if the given axioms are insufficient to produce a logically sound answer, you must **formally declare** — in a structured list — each specific piece of missing data that would be required to resolve the query. You are explicitly forbidden from estimating, inferring, or fabricating any values not directly stated.

**Axioms:**

1. System S has four processing nodes: N1, N2, N3, N4.
2. Each node consumes power proportional to its active task load.
3. Node N1 is currently running at 70% task load.
4. Node N3 failed at T=0 and offloaded its tasks to N2 and N4 in equal proportion.
5. The total system power budget is 500 watts.
6. When any node exceeds 90% task load, it triggers a thermal throttle event.

**Query:** Will a thermal throttle event occur in the system as a result of N3's failure?

Respond in one of exactly two formats:

**Format A** (if answerable): State `ANSWERABLE:` followed by your full logical derivation and conclusion.

**Format B** (if not answerable): State `INSUFFICIENT DATA:` followed by a numbered list where each item names one specific missing variable or fact, describes what it represents, and explains why its absence blocks the query's resolution. No inferences. No estimates.

---'''
},
"p04": {
    "regime": "dimensionality_compression",
    "budget": 128,
    "prompt": r'''Describe the complete process by which a central bank executes an open market operation to contract the money supply. Your description must consist of **exactly three sentences**. Each sentence must be a single, grammatically complete declarative statement. No sentence may be subdivided with semicolons into functional sub-sentences. No bullet points, numbered steps, headers, or supplementary text of any kind are permitted outside the three sentences.

The three-sentence constraint is hard: responses containing two sentences or four or more sentences are non-compliant.

---'''
},
}

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def count_sentences(text: str) -> int:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return len([p for p in parts if p.strip()])

def parse_json_object_only(text: str):
    s = text.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None, False
    try:
        return json.loads(s), True
    except Exception:
        return None, False

def validate_p01(text: str) -> dict[str, Any]:
    t = text.strip()
    obj, ok = parse_json_object_only(t)
    content_pass = False
    if ok:
        try:
            content_pass = (
                obj.get("primary_coolant_temp_celsius") in [847, 847.0]
                and obj.get("crew_count") == 9
                and abs(float(obj.get("avg_radiation_dose_mSv", -999)) - 4.7) < 1e-9
            )
        except Exception:
            content_pass = False
    semantic_content = False
    for m in re.finditer(r"\{[^{}]*\}", t, re.S):
        try:
            cand = json.loads(m.group(0))
            if (cand.get("primary_coolant_temp_celsius") in [847, 847.0]
                and cand.get("crew_count") == 9
                and abs(float(cand.get("avg_radiation_dose_mSv", -999)) - 4.7) < 1e-9):
                semantic_content = True
        except Exception:
            pass
    return {
        "format_pass": bool(ok),
        "content_pass": bool(content_pass),
        "semantic_content_pass": bool(semantic_content),
        "exact_answer_pass": bool(ok and content_pass),
        "constraint_violations": [] if ok else ["json_object_only"],
    }

def validate_p03(text: str) -> dict[str, Any]:
    t = text.strip(); low = t.lower()
    format_pass = t.startswith("INSUFFICIENT DATA:") or t.startswith("ANSWERABLE:")
    content_pass = t.startswith("INSUFFICIENT DATA:") and any(x in low for x in ["n2","n4","n3"]) and any(x in low for x in ["load","task"])
    return {
        "format_pass": bool(format_pass),
        "content_pass": bool(content_pass),
        "semantic_content_pass": bool(content_pass),
        "exact_answer_pass": bool(content_pass),
        "constraint_violations": [] if format_pass else ["required_prefix"],
    }

def validate_p04(text: str) -> dict[str, Any]:
    t = text.strip(); low=t.lower(); n_sent=count_sentences(t)
    format_pass = (n_sent == 3) and (';' not in t) and not re.search(r"(?m)^\s*[-*0-9]+[.)]", t)
    content_pass = ('central bank' in low) and any(x in low for x in ['sell','sells','selling']) and any(x in low for x in ['reserves','money supply','liquidity'])
    return {
        "format_pass": bool(format_pass),
        "content_pass": bool(content_pass),
        "semantic_content_pass": bool(content_pass),
        "exact_answer_pass": bool(format_pass and content_pass),
        "sentence_count": n_sent,
        "constraint_violations": ([] if n_sent == 3 else [f"sentence_count:{n_sent}"])
    }

VALIDATORS: dict[str, Callable[[str], dict[str, Any]]] = {"p01":validate_p01,"p03":validate_p03,"p04":validate_p04}

def l3_prompt(problem: str, l1: str, l2: str) -> str:
    return (
        "ORIGINAL PROBLEM:\n" + problem + "\n\n"
        "INDEPENDENT PROCEDURAL ATTEMPT L1:\n" + l1 + "\n\n"
        "INDEPENDENT PROCEDURAL ATTEMPT L2:\n" + l2 + "\n\n"
        "INTERNAL ORCHESTRATION CONTRACT — mandatory. Your entire response must begin with the literal token <RAW> "
        "and contain exactly this structure: <RAW>first complete new solution</RAW><INFORMED>final enriched solution</INFORMED>. "
        "Do not put Markdown fences around the XML tags. The content INSIDE <INFORMED> must obey the ORIGINAL PROBLEM's "
        "requested user-facing output contract exactly. Do not mention any configurational or parallel solver."
    )

def extract_informed(text: str) -> tuple[str|None, bool]:
    m = re.search(r"<INFORMED>(.*?)</INFORMED>", text, flags=re.S|re.I)
    if not m:
        return None, False
    return m.group(1).strip(), True

def pairwise(a: bool, b: bool) -> str:
    if a and not b: return "P_BETTER"
    if b and not a: return "C_BETTER"
    return "TIE"

def update_alpha(alpha: dict[str,float], outcome: str) -> None:
    alpha[outcome] += 1.0

def posterior(alpha: dict[str,float]) -> dict[str,float]:
    s=sum(alpha.values())
    return {k:v/s for k,v in alpha.items()}

def run_case(model, tokenizer, pid: str, outdir: Path) -> dict[str,Any]:
    spec=PROMPTS[pid]; prompt=spec["prompt"]; budget=int(spec["budget"])
    l1=base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,seed=SEEDS["L1"],max_new_tokens=budget)
    l2=base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,seed=SEEDS["L2"],max_new_tokens=budget)
    meta_budget=max(256, budget+192)
    l3=base.generate(model,tokenizer,prompt=l3_prompt(prompt,l1["text"],l2["text"]),system_prompt=(
        "You are the third and final PROCEDURAL orchestration pass. Follow the INTERNAL ORCHESTRATION CONTRACT literally. "
        "The XML tags are internal metadata. Only the content inside <INFORMED> is the P candidate."
    ),seed=SEEDS["L3"],max_new_tokens=meta_budget)
    p_final, wrapper_ok=extract_informed(l3["text"])

    proc=base.TALMMassRightSoftProcessor(base.TALMMassRightSoftConfig())
    c=base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_C,seed=SEEDS["C"],processor=proc,max_new_tokens=budget)
    c_final=c["text"].strip()

    candidate_payload={
        "prompt_id":pid,"regime":spec["regime"],"source_budget":budget,"l3_meta_budget":meta_budget,
        "P":{"L1":l1,"L2":l2,"L3":l3,"wrapper_compliance":wrapper_ok,"final_text":p_final},
        "C":{"carrier":"talm_mass_right_soft","run":c,"final_text":c_final,"diagnostics":proc.diagnostics},
    }
    p_hash=digest(candidate_payload["P"]); c_hash=digest(candidate_payload["C"])
    freeze=digest({"prompt_id":pid,"P":p_hash,"C":c_hash})
    candidate_payload["hashes"]={"P":p_hash,"C":c_hash,"freeze":freeze}
    (outdir/f"{pid}_candidates.json").write_text(json.dumps(candidate_payload,ensure_ascii=False,indent=2),encoding="utf-8")

    decision={
        "schema":"cfl-macro-pc-multicase-decision/v0.6","created_at":utcnow(),"prompt_id":pid,
        "candidate_freeze_hash":freeze,"decision":"BASELINE","authority_transfer":False,
        "outcome_visible_at_decision":False,
        "rationale":["macro authority remains shadow/warmup","one case cannot grant authority","outcome withheld until decision freeze"],
    }
    decision["sha256"]=digest(decision)
    (outdir/f"{pid}_decision_frozen.json").write_text(json.dumps(decision,indent=2),encoding="utf-8")

    val=VALIDATORS[pid]
    p_eval = val(p_final) if p_final is not None else {
        "format_pass":False,"content_pass":False,"semantic_content_pass":False,"exact_answer_pass":False,
        "constraint_violations":["P_L3_WRAPPER_FAILURE"],"not_admissible_as_P_candidate":True,
    }
    c_eval=val(c_final)
    paired_admissible = p_final is not None
    outcomes = (
        {
            "content": pairwise(bool(p_eval.get("semantic_content_pass",p_eval["content_pass"])), bool(c_eval.get("semantic_content_pass",c_eval["content_pass"]))),
            "format": pairwise(bool(p_eval["format_pass"]),bool(c_eval["format_pass"])),
            "exact": pairwise(bool(p_eval["exact_answer_pass"]),bool(c_eval["exact_answer_pass"])),
        }
        if paired_admissible
        else {"content":"UNRESOLVED","format":"UNRESOLVED","exact":"UNRESOLVED"}
    )
    outcome={
        "schema":"cfl-macro-pc-multicase-outcome/v0.6","created_at":utcnow(),"prompt_id":pid,"regime":spec["regime"],
        "source_notebook":SOURCE_NOTEBOOK,"source_budget":budget,"decision_sha256_before_outcome":decision["sha256"],
        "candidate_freeze_hash":freeze,"P":p_eval,"C":c_eval,"paired_admissible":paired_admissible,"pairwise":outcomes,
    }
    outcome["sha256"]=digest(outcome)
    (outdir/f"{pid}_outcome.json").write_text(json.dumps(outcome,indent=2),encoding="utf-8")
    return {"candidate":candidate_payload,"decision":decision,"outcome":outcome}

def main() -> int:
    outdir=Path("macro_pc_v06_artifact"); outdir.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
    tokenizer=AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token_id is None: tokenizer.pad_token_id=tokenizer.eos_token_id
    model=AutoModelForCausalLM.from_pretrained(MODEL_ID,torch_dtype=torch.float32,low_cpu_mem_usage=True)
    model.eval()

    global_prior={axis:{"P_BETTER":1.0,"TIE":1.0,"C_BETTER":1.0} for axis in ["content","format","exact"]}
    category_alpha={axis:{"P_BETTER":1.0,"TIE":1.0,"C_BETTER":1.0} for axis in ["content","format","exact"]}
    cases={}
    paired_evidence_mass=0
    for pid in ["p01","p03","p04"]:
        result=run_case(model,tokenizer,pid,outdir); cases[pid]=result
        if result["outcome"]["paired_admissible"]:
            paired_evidence_mass += 1
            for axis,o in result["outcome"]["pairwise"].items():
                update_alpha(category_alpha[axis],o)

    successor={
        "schema":"cfl-macro-pc-multicase-successor/v0.6","created_at":utcnow(),"model_id":MODEL_ID,
        "namespace":"MACRO_P_C_AUTHORITY::Qwen2.5-0.5B-Instruct::deterministic_constraint",
        "cases":["p01","p03","p04"],"unique_paired_evidence_mass":paired_evidence_mass,
        "global_macro_prior_before":global_prior,"global_macro_prior_after":global_prior,"global_macro_prior_changed":False,
        "local_category_alpha":category_alpha,
        "local_category_posterior":{axis:posterior(a) for axis,a in category_alpha.items()},
        "authority_transfer":False,"status":"SHADOW_MULTICASE_WARMUP",
        "note":"Only cases with both P and C candidates are allowed to update the paired posterior; producer failures remain diagnostic-only. No universal P/C authority is granted."
    }
    successor["sha256"]=digest(successor)
    (outdir/"successor_local_multicase_v1.json").write_text(json.dumps(successor,indent=2),encoding="utf-8")

    zpost={pid:{
        "regime":cases[pid]["outcome"]["regime"],
        "P":{k:v for k,v in cases[pid]["outcome"]["P"].items() if k.endswith("pass") or k in ["constraint_violations"]},
        "C":{k:v for k,v in cases[pid]["outcome"]["C"].items() if k.endswith("pass") or k in ["constraint_violations"]},
        "pairwise":cases[pid]["outcome"]["pairwise"],"authority_transfer":False
    } for pid in cases}
    (outdir/"z_post_multicase.json").write_text(json.dumps(zpost,indent=2),encoding="utf-8")

    head="0"*64; events=[]
    for pid in ["p01","p03","p04"]:
        r=cases[pid]
        for et,payload in [
            ("CANDIDATES_FROZEN",{"prompt_id":pid,"freeze":r["candidate"]["hashes"]["freeze"]}),
            ("DECISION_FROZEN",{"prompt_id":pid,"decision_sha256":r["decision"]["sha256"]}),
            ("OUTCOME_RECORDED",{"prompt_id":pid,"outcome_sha256":r["outcome"]["sha256"],"pairwise":r["outcome"]["pairwise"]}),
        ]:
            ev={"index":len(events),"event_type":et,"created_at":utcnow(),"payload":payload,"prev_hash":head}; ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    ev={"index":len(events),"event_type":"LOCAL_MULTICASE_SUCCESSOR_RELEASED","created_at":utcnow(),"payload":{"successor_sha256":successor["sha256"],"global_macro_prior_changed":False},"prev_hash":head}; ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    with (outdir/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:f.write(canonical_json(ev)+"\n")

    manifest={
        "schema":"cfl-macro-pc-multicase-gate/v0.6","created_at":utcnow(),"status":"PASS_SHADOW_MULTICASE",
        "model_id":MODEL_ID,"source_notebook":SOURCE_NOTEBOOK,"cases":["p01","p03","p04"],"seeds":SEEDS,
        "real_model_execution":True,"real_TALM_execution":True,"synthetic_observations":False,
        "outcomes_revealed_only_after_decision_freeze":True,"global_macro_prior_changed":False,"authority_transfer":False,
        "successor_sha256":successor["sha256"],"ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(outdir.glob("*")):
        if p.is_file() and p.name!="manifest.json":manifest.setdefault("files",{})[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (outdir/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

    summary={
        "status":manifest["status"],"cases":{},"local_category_posterior":successor["local_category_posterior"],
        "global_macro_prior_changed":False,"authority_transfer":False,"successor_sha256":successor["sha256"],"ledger_head_hash":head,
    }
    for pid,r in cases.items():
        summary["cases"][pid]={
            "P_wrapper":r["candidate"]["P"]["wrapper_compliance"],
            "P":r["outcome"]["P"],"C":r["outcome"]["C"],"pairwise":r["outcome"]["pairwise"]
        }
    print(json.dumps(summary,indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())
