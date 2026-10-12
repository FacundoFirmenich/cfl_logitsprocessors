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
import run_macro_pc_gate_v06 as v6

MODEL_ID = v6.MODEL_ID
SOURCE_NOTEBOOK = v6.SOURCE_NOTEBOOK
PROMPTS = v6.PROMPTS
VALIDATORS = v6.VALIDATORS
SYSTEM_P_BASE = v6.SYSTEM_P_BASE
SYSTEM_C = v6.SYSTEM_C

SEEDS = {
    "L1": 101,
    "L2": 202,
    "L3_RAW": 303,
    "L3_INFORMED": 304,
    "C": 404,
}

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def pairwise(a: bool, b: bool) -> str:
    if a and not b:
        return "P_BETTER"
    if b and not a:
        return "C_BETTER"
    return "TIE"

def update_alpha(alpha: dict[str,float], outcome: str) -> None:
    alpha[outcome] += 1.0

def posterior(alpha: dict[str,float]) -> dict[str,float]:
    s = sum(alpha.values())
    return {k: v/s for k,v in alpha.items()}

def l3_raw_prompt(problem: str, l1: str, l2: str) -> str:
    return (
        "ORIGINAL PROBLEM:\n" + problem + "\n\n"
        "PROCEDURAL ATTEMPT L1:\n" + l1 + "\n\n"
        "PROCEDURAL ATTEMPT L2:\n" + l2 + "\n\n"
        "THIRD-STAGE RAW SUBPHASE. Solve the ORIGINAL PROBLEM anew. "
        "Return only the answer requested by the ORIGINAL PROBLEM, with no commentary about L1, L2, stages, "
        "or orchestration. Obey the ORIGINAL PROBLEM's output contract exactly."
    )

def l3_informed_prompt(problem: str, l1: str, l2: str, l3_raw: str) -> str:
    return (
        "ORIGINAL PROBLEM:\n" + problem + "\n\n"
        "PROCEDURAL ATTEMPT L1:\n" + l1 + "\n\n"
        "PROCEDURAL ATTEMPT L2:\n" + l2 + "\n\n"
        "THIRD-STAGE RAW RESOLUTION:\n" + l3_raw + "\n\n"
        "THIRD-STAGE INFORMED SUBPHASE. Produce the final enriched resolution of the ORIGINAL PROBLEM after "
        "checking the three prior resolutions. Return only the answer requested by the ORIGINAL PROBLEM. "
        "Do not mention the prior attempts, stages, reconciliation, or orchestration. "
        "Obey the ORIGINAL PROBLEM's user-facing output contract exactly."
    )

def run_case(model, tokenizer, pid: str, outdir: Path) -> dict[str,Any]:
    spec = PROMPTS[pid]
    prompt = spec["prompt"]
    budget = int(spec["budget"])

    l1 = base.generate(
        model, tokenizer, prompt=prompt, system_prompt=SYSTEM_P_BASE,
        seed=SEEDS["L1"], max_new_tokens=budget
    )
    l2 = base.generate(
        model, tokenizer, prompt=prompt, system_prompt=SYSTEM_P_BASE,
        seed=SEEDS["L2"], max_new_tokens=budget
    )
    l3_raw = base.generate(
        model, tokenizer,
        prompt=l3_raw_prompt(prompt, l1["text"], l2["text"]),
        system_prompt=(
            "You are inside the third PROCEDURAL stage, raw subphase. "
            "Solve the complete original problem and output only its requested answer format."
        ),
        seed=SEEDS["L3_RAW"], max_new_tokens=budget
    )
    l3_informed = base.generate(
        model, tokenizer,
        prompt=l3_informed_prompt(prompt, l1["text"], l2["text"], l3_raw["text"]),
        system_prompt=(
            "You are inside the third PROCEDURAL stage, informed subphase. "
            "Return the final complete answer only in the original problem's requested format."
        ),
        seed=SEEDS["L3_INFORMED"], max_new_tokens=budget
    )
    p_final = l3_informed["text"].strip()
    p_materialized = bool(p_final)

    proc = base.TALMMassRightSoftProcessor(base.TALMMassRightSoftConfig())
    c_run = base.generate(
        model, tokenizer, prompt=prompt, system_prompt=SYSTEM_C,
        seed=SEEDS["C"], processor=proc, max_new_tokens=budget
    )
    c_final = c_run["text"].strip()
    c_materialized = bool(c_final)

    candidate_payload = {
        "schema": "cfl-macro-pc-two-phase-l3-candidates/v0.7",
        "created_at": utcnow(),
        "prompt_id": pid,
        "regime": spec["regime"],
        "source_budget": budget,
        "P": {
            "L1": l1,
            "L2": l2,
            "L3_raw": l3_raw,
            "L3_informed": l3_informed,
            "final_text": p_final,
            "materialized": p_materialized,
            "orchestration": "TWO_PHASE_THIRD_STAGE",
        },
        "C": {
            "carrier": "talm_mass_right_soft",
            "run": c_run,
            "final_text": c_final,
            "materialized": c_materialized,
            "talm_diagnostics": proc.diagnostics,
        },
    }
    p_hash = digest(candidate_payload["P"])
    c_hash = digest(candidate_payload["C"])
    freeze = digest({"prompt_id":pid, "P":p_hash, "C":c_hash, "protocol":"v0.7"})
    candidate_payload["hashes"] = {"P":p_hash, "C":c_hash, "freeze":freeze}
    (outdir/f"{pid}_candidates.json").write_text(
        json.dumps(candidate_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    decision = {
        "schema":"cfl-macro-pc-decision/v0.7",
        "created_at":utcnow(),
        "prompt_id":pid,
        "candidate_freeze_hash":freeze,
        "decision":"BASELINE",
        "authority_transfer":False,
        "outcome_visible_at_decision":False,
        "rationale":[
            "v0.7 is a producer-fidelity and local-calibration shadow gate",
            "source validator outcome is withheld until after candidate and decision freeze",
            "no single or three-case batch grants operational authority",
        ],
    }
    decision["sha256"] = digest(decision)
    (outdir/f"{pid}_decision_frozen.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )

    validator = VALIDATORS[pid]
    p_eval = validator(p_final) if p_materialized else {
        "format_pass":False, "content_pass":False, "semantic_content_pass":False,
        "exact_answer_pass":False, "constraint_violations":["P_CANDIDATE_EMPTY"]
    }
    c_eval = validator(c_final) if c_materialized else {
        "format_pass":False, "content_pass":False, "semantic_content_pass":False,
        "exact_answer_pass":False, "constraint_violations":["C_CANDIDATE_EMPTY"]
    }

    paired_admissible = p_materialized and c_materialized
    if paired_admissible:
        pair = {
            "source_content": pairwise(bool(p_eval["content_pass"]), bool(c_eval["content_pass"])),
            "source_format": pairwise(bool(p_eval["format_pass"]), bool(c_eval["format_pass"])),
            "source_exact": pairwise(bool(p_eval["exact_answer_pass"]), bool(c_eval["exact_answer_pass"])),
        }
    else:
        pair = {"source_content":"UNRESOLVED","source_format":"UNRESOLVED","source_exact":"UNRESOLVED"}

    outcome = {
        "schema":"cfl-macro-pc-outcome/v0.7",
        "created_at":utcnow(),
        "prompt_id":pid,
        "regime":spec["regime"],
        "source_notebook":SOURCE_NOTEBOOK,
        "source_budget":budget,
        "decision_sha256_before_outcome":decision["sha256"],
        "candidate_freeze_hash":freeze,
        "P":p_eval,
        "C":c_eval,
        "paired_admissible":paired_admissible,
        "pairwise":pair,
    }
    outcome["sha256"] = digest(outcome)
    (outdir/f"{pid}_outcome.json").write_text(
        json.dumps(outcome, indent=2), encoding="utf-8"
    )
    return {"candidate":candidate_payload,"decision":decision,"outcome":outcome}

def main() -> int:
    outdir = Path("macro_pc_v07_artifact")
    outdir.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, low_cpu_mem_usage=True
    )
    model.eval()

    axes = ["source_content","source_format","source_exact"]
    alpha = {axis:{"P_BETTER":1.0,"TIE":1.0,"C_BETTER":1.0} for axis in axes}
    cases = {}
    paired_mass = 0
    p_materialized = 0

    for pid in ["p01","p03","p04"]:
        r = run_case(model, tokenizer, pid, outdir)
        cases[pid] = r
        if r["candidate"]["P"]["materialized"]:
            p_materialized += 1
        if r["outcome"]["paired_admissible"]:
            paired_mass += 1
            for axis, result in r["outcome"]["pairwise"].items():
                update_alpha(alpha[axis], result)

    local_posterior = {axis:posterior(a) for axis,a in alpha.items()}
    successor = {
        "schema":"cfl-macro-pc-two-phase-l3-successor/v0.7",
        "created_at":utcnow(),
        "model_id":MODEL_ID,
        "protocol":"P_L1_L2_L3_TWO_PHASE_RAW_INFORMED__C_TALM_MASS_RIGHT_SOFT",
        "namespace":"MACRO_P_C_AUTHORITY::Qwen2.5-0.5B-Instruct::deterministic_constraint::v0.7",
        "cases":["p01","p03","p04"],
        "executed_cases":3,
        "P_candidate_materialization":p_materialized,
        "P_candidate_materialization_rate":p_materialized/3.0,
        "paired_admissible_cases":paired_mass,
        "alpha":alpha,
        "posterior_mean":local_posterior,
        "global_macro_prior_changed":False,
        "authority_transfer":False,
        "status":"SHADOW_LOCAL_MULTICASE",
    }
    successor["sha256"] = digest(successor)
    (outdir/"successor_local_v1.json").write_text(
        json.dumps(successor, indent=2), encoding="utf-8"
    )

    zpost = {}
    for pid,r in cases.items():
        zpost[pid] = {
            "regime":r["outcome"]["regime"],
            "P_materialized":r["candidate"]["P"]["materialized"],
            "C_materialized":r["candidate"]["C"]["materialized"],
            "P_eval":r["outcome"]["P"],
            "C_eval":r["outcome"]["C"],
            "pairwise":r["outcome"]["pairwise"],
            "authority_transfer":False,
        }
    (outdir/"z_post_multicase.json").write_text(
        json.dumps(zpost, indent=2), encoding="utf-8"
    )

    head = "0"*64
    events = []
    for pid in ["p01","p03","p04"]:
        r = cases[pid]
        for event_type,payload in [
            ("CANDIDATES_FROZEN",{"prompt_id":pid,"freeze":r["candidate"]["hashes"]["freeze"]}),
            ("DECISION_FROZEN",{"prompt_id":pid,"decision_sha256":r["decision"]["sha256"]}),
            ("OUTCOME_RECORDED",{"prompt_id":pid,"outcome_sha256":r["outcome"]["sha256"],"pairwise":r["outcome"]["pairwise"]}),
        ]:
            ev={"index":len(events),"event_type":event_type,"created_at":utcnow(),"payload":payload,"prev_hash":head}
            ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    ev={"index":len(events),"event_type":"LOCAL_SUCCESSOR_RELEASED","created_at":utcnow(),
        "payload":{"successor_sha256":successor["sha256"],"global_macro_prior_changed":False,"authority_transfer":False},
        "prev_hash":head}
    ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    with (outdir/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:
            f.write(canonical_json(ev)+"\n")

    manifest = {
        "schema":"cfl-macro-pc-two-phase-l3-gate/v0.7",
        "created_at":utcnow(),
        "status":"PASS_SHADOW",
        "model_id":MODEL_ID,
        "source_notebook":SOURCE_NOTEBOOK,
        "seeds":SEEDS,
        "real_model_execution":True,
        "real_TALM_execution":True,
        "synthetic_observations":False,
        "producer_protocol":"P third stage split into RAW then INFORMED subphases; final candidate is direct L3_INFORMED output",
        "P_candidate_materialization_rate":p_materialized/3.0,
        "paired_admissible_cases":paired_mass,
        "global_macro_prior_changed":False,
        "authority_transfer":False,
        "successor_sha256":successor["sha256"],
        "ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(outdir.glob("*")):
        if p.is_file() and p.name!="manifest.json":
            manifest.setdefault("files",{})[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
    (outdir/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

    summary = {
        "status":manifest["status"],
        "P_candidate_materialization_rate":p_materialized/3.0,
        "paired_admissible_cases":paired_mass,
        "cases":{},
        "local_posterior":local_posterior,
        "global_macro_prior_changed":False,
        "authority_transfer":False,
        "successor_sha256":successor["sha256"],
        "ledger_head_hash":head,
    }
    for pid,r in cases.items():
        summary["cases"][pid] = {
            "P_final":r["candidate"]["P"]["final_text"],
            "C_final":r["candidate"]["C"]["final_text"],
            "P_eval":r["outcome"]["P"],
            "C_eval":r["outcome"]["C"],
            "pairwise":r["outcome"]["pairwise"],
        }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
