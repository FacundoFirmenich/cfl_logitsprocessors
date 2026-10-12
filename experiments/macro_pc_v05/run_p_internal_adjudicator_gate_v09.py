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

def vector(ev: dict[str,Any]) -> dict[str,int]:
    return {
        "semantic": int(bool(ev.get("semantic_content_pass", ev.get("content_pass", False)))),
        "format": int(bool(ev.get("format_pass", False))),
        "exact": int(bool(ev.get("exact_answer_pass", False))),
    }

def dominates(a: dict[str,int], b: dict[str,int]) -> bool:
    keys = ["semantic","format","exact"]
    return all(a[k] >= b[k] for k in keys) and any(a[k] > b[k] for k in keys)

def pareto_frontier(vectors: dict[str,dict[str,int]]) -> list[str]:
    frontier = []
    for s, v in vectors.items():
        if not any(other != s and dominates(ov, v) for other, ov in vectors.items()):
            frontier.append(s)
    return frontier

def anti_regression_adjudicate(vectors: dict[str,dict[str,int]]) -> dict[str,Any]:
    """Deterministic, non-compensatory selector/abstainer.

    Rule is frozen before the run:
    1) if L3_informed is not Pareto-dominated by a prior stage, retain it;
    2) if dominated, compute the Pareto frontier across all stages;
    3) if a unique frontier stage exists, select it;
    4) otherwise retain the frontier as TOPK_INTERNAL and abstain from a single P answer.
    """
    l3 = vectors["L3_informed"]
    prior_dominators = [s for s in ["L1","L2","L3_raw"] if dominates(vectors[s], l3)]
    frontier = pareto_frontier(vectors)

    if not prior_dominators:
        return {
            "decision":"SELECT",
            "selected_stage":"L3_informed",
            "frontier":frontier,
            "blocked_l3_regression":False,
            "rationale":"L3_informed is not Pareto-dominated by any prior P stage.",
        }

    if len(frontier) == 1:
        return {
            "decision":"SELECT",
            "selected_stage":frontier[0],
            "frontier":frontier,
            "blocked_l3_regression":True,
            "rationale":"L3_informed is dominated; unique Pareto-frontier predecessor selected.",
        }

    return {
        "decision":"TOPK_INTERNAL_ABSTAIN",
        "selected_stage":None,
        "frontier":frontier,
        "blocked_l3_regression":True,
        "rationale":"L3_informed is dominated and multiple incomparable Pareto-frontier stages remain; no synthesis is permitted.",
    }

def generate_case(model, tokenizer, pid: str) -> dict[str,Any]:
    spec = PROMPTS[pid]
    prompt = spec["prompt"]
    budget = int(spec["budget"])

    l1 = base.generate(model, tokenizer, prompt=prompt, system_prompt=SYSTEM_P_BASE,
                       seed=SEEDS["L1"], max_new_tokens=budget)
    l2 = base.generate(model, tokenizer, prompt=prompt, system_prompt=SYSTEM_P_BASE,
                       seed=SEEDS["L2"], max_new_tokens=budget)
    l3_raw = base.generate(
        model, tokenizer,
        prompt=v7.l3_raw_prompt(prompt, l1["text"], l2["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, raw subphase. Solve the complete original problem and output only its requested answer format.",
        seed=SEEDS["L3_RAW"], max_new_tokens=budget
    )
    l3_informed = base.generate(
        model, tokenizer,
        prompt=v7.l3_informed_prompt(prompt, l1["text"], l2["text"], l3_raw["text"]),
        system_prompt="You are inside the third PROCEDURAL stage, informed subphase. Return the final complete answer only in the original problem's requested format.",
        seed=SEEDS["L3_INFORMED"], max_new_tokens=budget
    )
    return {
        "prompt_id":pid,
        "regime":spec["regime"],
        "source_budget":budget,
        "stages":{"L1":l1,"L2":l2,"L3_raw":l3_raw,"L3_informed":l3_informed},
    }

def main() -> int:
    out = Path("macro_pc_v09_artifact")
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
    selected_regressions = 0
    blocked_regressions = 0
    single_p_available = 0
    abstentions = 0

    for pid in ["p01","p03","p04"]:
        g = generate_case(model, tok, pid)
        verifier = VALIDATORS[pid]
        evals = {}
        vectors = {}
        for stage in STAGES:
            txt = g["stages"][stage]["text"].strip()
            ev = verifier(txt)
            evals[stage] = ev
            vectors[stage] = vector(ev)

        ap = anti_regression_adjudicate(vectors)

        if ap["decision"] == "SELECT":
            selected_stage = ap["selected_stage"]
            selected_text = g["stages"][selected_stage]["text"].strip()
            selected_vector = vectors[selected_stage]
            if any(dominates(vectors[s], selected_vector) for s in STAGES if s != selected_stage):
                selected_regressions += 1
            single_p_available += 1
        else:
            selected_stage = None
            selected_text = None
            selected_vector = None
            abstentions += 1

        if ap["blocked_l3_regression"]:
            blocked_regressions += 1

        record = {
            "schema":"cfl-p-internal-adjudicator-case/v0.9",
            "created_at":utcnow(),
            "prompt_id":pid,
            "regime":g["regime"],
            "source_budget":g["source_budget"],
            "seeds":SEEDS,
            "stages":g["stages"],
            "evaluations":evals,
            "vectors":vectors,
            "A_P":ap,
            "P_frozen":{
                "available":selected_text is not None,
                "selected_stage":selected_stage,
                "text":selected_text,
                "vector":selected_vector,
            },
        }
        record["sha256"] = digest(record)
        cases[pid] = record
        (out/f"{pid}_A_P.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    summary = {
        "schema":"cfl-p-internal-adjudicator-summary/v0.9",
        "created_at":utcnow(),
        "model_id":MODEL_ID,
        "source_notebook":SOURCE_NOTEBOOK,
        "cases":["p01","p03","p04"],
        "rule":{
            "type":"deterministic_noncompensatory_pareto_guard",
            "default":"retain L3_informed only when not dominated",
            "dominated_l3":"select unique Pareto frontier stage, else TOPK_INTERNAL_ABSTAIN",
            "semantic_rewrite":False,
            "averaging":False,
        },
        "counts":{
            "executed_cases":3,
            "single_P_available":single_p_available,
            "abstentions":abstentions,
            "blocked_L3_regressions":blocked_regressions,
            "selected_regressions":selected_regressions,
        },
        "case_decisions":{
            pid:{
                "decision":cases[pid]["A_P"]["decision"],
                "selected_stage":cases[pid]["A_P"]["selected_stage"],
                "frontier":cases[pid]["A_P"]["frontier"],
                "blocked_l3_regression":cases[pid]["A_P"]["blocked_l3_regression"],
            } for pid in cases
        },
        "gate_pass": selected_regressions == 0 and blocked_regressions >= 1,
        "availability_rate":single_p_available/3.0,
        "authority_transfer":False,
        "global_macro_prior_changed":False,
    }
    summary["sha256"] = digest(summary)
    (out/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")

    zpost = {
        "schema":"cfl-p-internal-adjudicator-zpost/v0.9",
        "created_at":utcnow(),
        "cases":{
            pid:{
                "regime":cases[pid]["regime"],
                "vectors":cases[pid]["vectors"],
                "A_P":cases[pid]["A_P"],
            } for pid in cases
        },
        "authority_transfer":False,
        "reading":(
            "A_P blocks observed L3 regression without rewriting content. "
            "Availability may decrease because incomparable internal frontiers are preserved rather than force-resolved."
        ),
    }
    zpost["sha256"] = digest(zpost)
    (out/"z_post.json").write_text(json.dumps(zpost,indent=2),encoding="utf-8")

    head = "0"*64
    events = []
    for pid in ["p01","p03","p04"]:
        for et,payload in [
            ("P_STAGES_FROZEN",{"prompt_id":pid,"case_sha256":cases[pid]["sha256"]}),
            ("A_P_DECISION_FROZEN",{"prompt_id":pid,"A_P":cases[pid]["A_P"]}),
            ("P_CANDIDATE_FROZEN",{"prompt_id":pid,"P_frozen":cases[pid]["P_frozen"]}),
        ]:
            ev={"index":len(events),"event_type":et,"created_at":utcnow(),"payload":payload,"prev_hash":head}
            ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    ev={"index":len(events),"event_type":"A_P_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"gate_pass":summary["gate_pass"],"zpost_sha256":zpost["sha256"]},
        "prev_hash":head}
    ev["hash"]=digest(ev); head=ev["hash"]; events.append(ev)
    with (out/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:
            f.write(canonical_json(ev)+"\n")

    manifest = {
        "schema":"cfl-p-internal-adjudicator-gate/v0.9",
        "created_at":utcnow(),
        "status":"PASS" if summary["gate_pass"] else "FAIL_WITH_EVIDENCE",
        "real_model_execution":True,
        "synthetic_observations":False,
        "model_id":MODEL_ID,
        "selected_regressions":selected_regressions,
        "blocked_L3_regressions":blocked_regressions,
        "availability_rate":summary["availability_rate"],
        "authority_transfer":False,
        "global_macro_prior_changed":False,
        "summary_sha256":summary["sha256"],
        "zpost_sha256":zpost["sha256"],
        "ledger_head_hash":head,
        "environment":{"python":sys.version,"platform":platform.platform(),"torch":torch.__version__,"transformers":transformers.__version__},
    }
    for p in sorted(out.glob("*")):
        if p.is_file() and p.name != "manifest.json":
            manifest.setdefault("files",{})[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

    print(json.dumps({"summary":summary,"zpost":zpost,"ledger_head_hash":head},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
