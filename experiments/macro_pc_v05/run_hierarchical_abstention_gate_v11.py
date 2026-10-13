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
import run_p_internal_adjudicator_gate_v09 as v09
import run_p_internal_ask_gate_v10 as v10

MODEL_ID = v7.MODEL_ID
SOURCE_NOTEBOOK = v7.SOURCE_NOTEBOOK
PROMPTS = v7.PROMPTS
VALIDATORS = v7.VALIDATORS
SYSTEM_P_BASE = v7.SYSTEM_P_BASE
SYSTEM_C = v7.SYSTEM_C
SEEDS = v7.SEEDS
STAGES = ["L1","L2","L3_raw","L3_informed"]

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def generate_full_case(model, tokenizer, pid: str) -> dict[str,Any]:
    spec = PROMPTS[pid]
    prompt = spec["prompt"]
    budget = int(spec["budget"])

    # P stages.
    l1 = base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,
                       seed=SEEDS["L1"],max_new_tokens=budget)
    l2 = base.generate(model,tokenizer,prompt=prompt,system_prompt=SYSTEM_P_BASE,
                       seed=SEEDS["L2"],max_new_tokens=budget)
    l3_raw = base.generate(
        model,tokenizer,
        prompt=v7.l3_raw_prompt(prompt,l1["text"],l2["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, raw subphase. Solve the complete original problem and output only its requested answer format.",
        seed=SEEDS["L3_RAW"],max_new_tokens=budget
    )
    l3_informed = base.generate(
        model,tokenizer,
        prompt=v7.l3_informed_prompt(prompt,l1["text"],l2["text"],l3_raw["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, informed subphase. Return the final complete answer only in the original problem's requested format.",
        seed=SEEDS["L3_INFORMED"],max_new_tokens=budget
    )
    p_stages = {"L1":l1,"L2":l2,"L3_raw":l3_raw,"L3_informed":l3_informed}

    verifier = VALIDATORS[pid]
    p_evals = {}
    p_vectors = {}
    for stage in STAGES:
        ev = verifier(p_stages[stage]["text"].strip())
        p_evals[stage] = ev
        p_vectors[stage] = v09.vector(ev)

    ap = v09.anti_regression_adjudicate(p_vectors)
    ask = None
    p_selected_stage = None
    p_final_text = None
    p_state = "ABSTAIN"

    if ap["decision"] == "SELECT":
        p_selected_stage = ap["selected_stage"]
        p_final_text = p_stages[p_selected_stage]["text"].strip()
        p_state = "AVAILABLE"
    else:
        ask = v10.ask_resolve(ap["frontier"], p_stages, pid)
        if ask["invoked"] and ask["decision"] == "SELECT":
            p_selected_stage = ask["selected_stage"]
            p_final_text = p_stages[p_selected_stage]["text"].strip()
            p_state = "AVAILABLE"
        else:
            p_state = "ABSTAIN"

    # Independent C candidate.
    proc = base.TALMMassRightSoftProcessor(base.TALMMassRightSoftConfig())
    c_run = base.generate(
        model,tokenizer,prompt=prompt,system_prompt=SYSTEM_C,
        seed=SEEDS["C"],processor=proc,max_new_tokens=budget
    )
    c_text = c_run["text"].strip()
    c_eval = verifier(c_text)

    return {
        "prompt_id":pid,
        "regime":spec["regime"],
        "source_budget":budget,
        "P":{
            "stages":p_stages,
            "evaluations":p_evals,
            "vectors":p_vectors,
            "A_P":ap,
            "ASK":ask,
            "state":p_state,
            "selected_stage":p_selected_stage,
            "final_text":p_final_text,
        },
        "C":{
            "carrier":"talm_mass_right_soft",
            "run":c_run,
            "text":c_text,
            "source_evaluation":c_eval,
            "talm_diagnostics":proc.diagnostics,
            "state":"AVAILABLE" if bool(c_text) else "UNAVAILABLE",
        },
    }

def symbolic_status(available: bool, source_eval: dict[str,Any] | None) -> str:
    if not available:
        return "UNAVAILABLE"
    if source_eval is None:
        return "UNRESOLVED"
    return "VALID" if bool(source_eval.get("exact_answer_pass",False)) else "INVALID_SOURCE_CONTRACT"

def macro_assess(process: str, available: bool, source_eval: dict[str,Any] | None,
                 custody_ok: bool) -> dict[str,Any]:
    sym = symbolic_status(available, source_eval)

    # Frozen macro jurisdiction policy for this gate.
    # Availability/symbolic/fidelity are case-observable.
    # Support/utility/transportability are explicitly NOT yet demonstrated
    # for the full macro P-vs-C authority problem.
    gates = {
        "availability": bool(available),
        "symbolic_contract": sym == "VALID",
        "fidelity_custody": bool(custody_ok),
        "macro_support": False,
        "macro_utility_risk": False,
        "macro_transportability": False,
    }
    eligible = all(gates.values())
    return {
        "process":process,
        "symbolic_status":sym,
        "gates":gates,
        "eligible_for_macro_authority":eligible,
        "survivor_bonus":False,
    }

def macro_decide(p_assess: dict[str,Any], c_assess: dict[str,Any],
                 baseline_authorized: bool=True) -> dict[str,Any]:
    p_ok = p_assess["eligible_for_macro_authority"]
    c_ok = c_assess["eligible_for_macro_authority"]

    if p_ok and c_ok:
        decision = "TOP2"
        rationale = "Both candidates satisfy all frozen macro gates; no forced winner."
    elif p_ok:
        decision = "APPLY_P"
        rationale = "Only P satisfies all frozen macro gates."
    elif c_ok:
        decision = "APPLY_C"
        rationale = "Only C satisfies all frozen macro gates."
    else:
        decision = "BASELINE" if baseline_authorized else "ABSTAIN"
        rationale = "No candidate satisfies all frozen macro authority gates."

    return {
        "decision":decision,
        "rationale":rationale,
        "P_eligible":p_ok,
        "C_eligible":c_ok,
        "baseline_authorized":baseline_authorized,
        "survivor_default_forbidden":True,
    }

def main() -> int:
    out = Path("macro_pc_v11_artifact")
    out.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(max(1,min(4,os.cpu_count() or 1)))
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    if tok.pad_token_id is None:
        tok.pad_token_id = tok.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID, torch_dtype=torch.float32, low_cpu_mem_usage=True
    )
    model.eval()

    cases = {}
    survivor_cases = 0
    survivor_auto_wins = 0
    unsafe_applies = 0

    for pid in ["p01","p03","p04"]:
        case = generate_full_case(model,tok,pid)

        # Freeze the producer state BEFORE macro assessment.
        producer_state = {
            "prompt_id":pid,
            "P_state":case["P"]["state"],
            "P_selected_stage":case["P"]["selected_stage"],
            "P_text_sha256":(
                hashlib.sha256(case["P"]["final_text"].encode()).hexdigest()
                if case["P"]["final_text"] is not None else None
            ),
            "C_state":case["C"]["state"],
            "C_text_sha256":hashlib.sha256(case["C"]["text"].encode()).hexdigest(),
        }
        producer_state["freeze_sha256"] = digest(producer_state)

        p_available = case["P"]["state"] == "AVAILABLE"
        p_eval = (
            VALIDATORS[pid](case["P"]["final_text"])
            if p_available and case["P"]["final_text"] is not None else None
        )
        c_available = case["C"]["state"] == "AVAILABLE"
        c_eval = case["C"]["source_evaluation"]

        p_assess = macro_assess("P",p_available,p_eval,custody_ok=True)
        c_assess = macro_assess("C",c_available,c_eval,custody_ok=True)

        decision = macro_decide(p_assess,c_assess,baseline_authorized=True)

        if not p_available and c_available:
            survivor_cases += 1
            if decision["decision"] == "APPLY_C":
                survivor_auto_wins += 1

        if decision["decision"] == "APPLY_P" and not p_assess["eligible_for_macro_authority"]:
            unsafe_applies += 1
        if decision["decision"] == "APPLY_C" and not c_assess["eligible_for_macro_authority"]:
            unsafe_applies += 1

        record = {
            "schema":"cfl-hierarchical-abstention-case/v1.1",
            "created_at":utcnow(),
            "prompt_id":pid,
            "regime":case["regime"],
            "source_budget":case["source_budget"],
            "producer":case,
            "producer_freeze":producer_state,
            "macro_assessment":{"P":p_assess,"C":c_assess},
            "macro_decision":decision,
        }
        record["sha256"] = digest(record)
        cases[pid] = record
        (out/f"{pid}_hierarchical_abstention.json").write_text(
            json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8"
        )

    p04 = cases["p04"]
    p04_critical_property = (
        p04["producer"]["P"]["state"] == "ABSTAIN"
        and p04["producer"]["C"]["state"] == "AVAILABLE"
        and bool(p04["producer"]["C"]["source_evaluation"].get("exact_answer_pass",False))
        and p04["macro_assessment"]["C"]["eligible_for_macro_authority"] is False
        and p04["macro_decision"]["decision"] in {"BASELINE","ABSTAIN"}
    )

    summary = {
        "schema":"cfl-hierarchical-abstention-summary/v1.1",
        "created_at":utcnow(),
        "model_id":MODEL_ID,
        "source_notebook":SOURCE_NOTEBOOK,
        "cases":["p01","p03","p04"],
        "frozen_macro_policy":{
            "survivor_bonus":False,
            "macro_support_demonstrated":False,
            "macro_utility_risk_calibrated":False,
            "macro_transportability_demonstrated":False,
            "baseline_authorized":True,
        },
        "counts":{
            "executed_cases":3,
            "survivor_cases_P_unavailable_C_available":survivor_cases,
            "survivor_auto_wins":survivor_auto_wins,
            "unsafe_applies":unsafe_applies,
        },
        "case_decisions":{
            pid:{
                "P_state":cases[pid]["producer"]["P"]["state"],
                "C_state":cases[pid]["producer"]["C"]["state"],
                "P_symbolic":cases[pid]["macro_assessment"]["P"]["symbolic_status"],
                "C_symbolic":cases[pid]["macro_assessment"]["C"]["symbolic_status"],
                "C_source_exact":bool(cases[pid]["producer"]["C"]["source_evaluation"].get("exact_answer_pass",False)),
                "macro_decision":cases[pid]["macro_decision"]["decision"],
            } for pid in cases
        },
        "p04_critical_property_pass":p04_critical_property,
        "gate_pass": (
            survivor_cases >= 1
            and survivor_auto_wins == 0
            and unsafe_applies == 0
            and p04_critical_property
        ),
        "authority_transfer":False,
        "global_macro_prior_changed":False,
    }
    summary["sha256"] = digest(summary)
    (out/"summary.json").write_text(
        json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8"
    )

    zpost = {
        "schema":"cfl-hierarchical-abstention-zpost/v1.1",
        "created_at":utcnow(),
        "p04":{
            "P_state":p04["producer"]["P"]["state"],
            "C_state":p04["producer"]["C"]["state"],
            "C_source_exact":bool(p04["producer"]["C"]["source_evaluation"].get("exact_answer_pass",False)),
            "C_macro_gates":p04["macro_assessment"]["C"]["gates"],
            "C_eligible":p04["macro_assessment"]["C"]["eligible_for_macro_authority"],
            "macro_decision":p04["macro_decision"]["decision"],
        },
        "authority_transfer":False,
        "reading":"P abstention propagates as missing authority, not negative evidence and not survivor bonus for C.",
    }
    zpost["sha256"] = digest(zpost)
    (out/"z_post.json").write_text(
        json.dumps(zpost,indent=2,ensure_ascii=False),encoding="utf-8"
    )

    head = "0"*64
    events=[]
    for pid in ["p01","p03","p04"]:
        rec = cases[pid]
        for et,payload in [
            ("PRODUCER_STATE_FROZEN",{"prompt_id":pid,"freeze_sha256":rec["producer_freeze"]["freeze_sha256"]}),
            ("MACRO_GATES_EVALUATED",{"prompt_id":pid,"assessment":rec["macro_assessment"]}),
            ("MACRO_DECISION_FROZEN",{"prompt_id":pid,"decision":rec["macro_decision"]}),
        ]:
            ev={"index":len(events),"event_type":et,"created_at":utcnow(),"payload":payload,"prev_hash":head}
            ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    ev={"index":len(events),"event_type":"HIERARCHICAL_ABSTENTION_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"gate_pass":summary["gate_pass"],"zpost_sha256":zpost["sha256"]},
        "prev_hash":head}
    ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)

    with (out/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:
            f.write(canonical_json(ev)+"\n")

    manifest = {
        "schema":"cfl-hierarchical-abstention-gate/v1.1",
        "created_at":utcnow(),
        "status":"PASS" if summary["gate_pass"] else "FAIL_WITH_EVIDENCE",
        "real_model_execution":True,
        "real_TALM_execution":True,
        "synthetic_observations":False,
        "survivor_bonus":False,
        "survivor_auto_wins":survivor_auto_wins,
        "unsafe_applies":unsafe_applies,
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "summary_sha256":summary["sha256"],
        "zpost_sha256":zpost["sha256"],
        "ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(out.glob("*")):
        if p.is_file() and p.name!="manifest.json":
            manifest.setdefault("files",{})[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"manifest.json").write_text(
        json.dumps(manifest,indent=2,ensure_ascii=False),encoding="utf-8"
    )

    print(json.dumps({"summary":summary,"zpost":zpost,"ledger_head_hash":head},indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
