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
from typing import Any

import torch
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_macro_pc_gate_v05 as base
import run_macro_pc_gate_v07 as v7
import run_p_internal_adjudicator_gate_v09 as v09

MODEL_ID = v7.MODEL_ID
SOURCE_NOTEBOOK = v7.SOURCE_NOTEBOOK
PROMPTS = v7.PROMPTS
VALIDATORS = v7.VALIDATORS
SYSTEM_P_BASE = v7.SYSTEM_P_BASE
SEEDS = v7.SEEDS
STAGES = ["L1","L2","L3_raw","L3_informed"]

# Frozen before execution. These sources define the independent p04 ASK semantics.
EXTERNAL_VERIFIER_SOURCES = [
    {
        "authority":"Federal Reserve Bank of New York",
        "title":"Open Market Operations: Key Concepts",
        "url":"https://www.newyorkfed.org/markets/openmarket_concepts",
        "fact":"Outright purchases add reserves; outright sales drain reserves."
    },
    {
        "authority":"Federal Reserve Bank of New York",
        "title":"What We Do",
        "url":"https://www.newyorkfed.org/aboutthefed/more-about-what-we-do",
        "fact":"The Fed adds credit when it buys Treasury securities and drains credit when it sells."
    },
    {
        "authority":"Federal Reserve Board",
        "title":"Implementing Monetary Policy in an Ample-Reserves Regime",
        "url":"https://www.federalreserve.gov/econres/notes/feds-notes/implementing-monetary-policy-in-an-ample-reserves-regime-maintaining-an-ample-quantity-of-reserves-note-2-of-3-20200828.html",
        "fact":"Purchases increase reserves; sales decrease reserves."
    },
]

def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def external_p04_verifier(text: str) -> dict[str,Any]:
    """Independent, conjunctive, non-compensatory verification-only ASK.

    It does not generate a replacement answer. It checks only necessary
    contractionary-OMO conditions frozen from authoritative external sources.
    """
    t = text.strip()
    low = t.lower()

    sale_instrument = bool(
        re.search(r"\b(sell|sells|selling|sale|sales|sold)\b", low)
        and re.search(r"\b(securit(?:y|ies)|bond(?:s)?|treasur(?:y|ies))\b", low)
    )
    contraction_verb = bool(
        re.search(r"\b(reduc(?:e|es|ed|ing)|decreas(?:e|es|ed|ing)|drain(?:s|ed|ing)?|contract(?:s|ed|ing)?|shrink(?:s|age|ing)?|tighten(?:s|ed|ing)?)\b", low)
    )
    contraction_object = bool(
        re.search(r"\b(reserve(?:s)?|liquidity|money supply|monetary base|credit|currency in circulation)\b", low)
    )
    explicit_contraction_effect = contraction_verb and contraction_object

    expansionary_patterns = [
        r"quantitative easing",
        r"lower(?:ing|s|ed)?\s+(?:the\s+)?(?:policy\s+|interest\s+)?rate",
        r"reduc(?:e|es|ed|ing)\s+(?:the\s+)?(?:policy\s+|interest\s+)?rate",
        r"stimulat(?:e|es|ed|ing)\s+(?:economic\s+)?activity",
        r"inject(?:s|ed|ing)?\s+liquidity",
        r"(?:buy|buys|buying|purchase|purchases|purchasing)\b.{0,100}\b(?:inject|increase|expand|boost)\b.{0,60}\b(?:liquidity|reserves|money supply|credit)",
    ]
    expansionary_contradictions = [
        pat for pat in expansionary_patterns if re.search(pat, low, flags=re.S)
    ]

    pass_all = sale_instrument and explicit_contraction_effect and not expansionary_contradictions
    return {
        "verifier":"EXTERNAL_P04_CONTRACTIONARY_OMO_NECESSARY_CONDITIONS_v1.0",
        "sale_of_securities":sale_instrument,
        "explicit_contraction_effect":explicit_contraction_effect,
        "contraction_verb_present":contraction_verb,
        "contraction_object_present":contraction_object,
        "expansionary_contradictions":expansionary_contradictions,
        "pass":bool(pass_all),
        "sources":EXTERNAL_VERIFIER_SOURCES,
    }

def generate_case(model, tokenizer, pid: str) -> dict[str,Any]:
    spec = PROMPTS[pid]
    prompt = spec["prompt"]
    budget = int(spec["budget"])
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
    return {
        "prompt_id":pid,
        "regime":spec["regime"],
        "source_budget":budget,
        "stages":{"L1":l1,"L2":l2,"L3_raw":l3_raw,"L3_informed":l3_informed},
    }

def ask_resolve(frontier: list[str], stages: dict[str,Any], pid: str) -> dict[str,Any]:
    if pid != "p04":
        return {
            "invoked":False,
            "decision":"NOT_APPLICABLE",
            "selected_stage":None,
            "frontier":frontier,
        }

    observations = {}
    passed = []
    for stage in frontier:
        obs = external_p04_verifier(stages[stage]["text"])
        observations[stage] = obs
        if obs["pass"]:
            passed.append(stage)

    if len(passed) == 1:
        decision = "SELECT"
        selected = passed[0]
        rationale = "Exactly one Pareto-frontier candidate passed the independent frozen verifier."
    elif len(passed) == 0:
        decision = "ABSTAIN_NO_VERIFIED_CANDIDATE"
        selected = None
        rationale = "No Pareto-frontier candidate passed all independent necessary conditions."
    else:
        decision = "ABSTAIN_MULTIPLE_VERIFIED_CANDIDATES"
        selected = None
        rationale = "More than one frontier candidate passed; independent verification did not uniquely resolve authority."

    return {
        "invoked":True,
        "verifier":"EXTERNAL_P04_CONTRACTIONARY_OMO_NECESSARY_CONDITIONS_v1.0",
        "frontier":frontier,
        "observations":observations,
        "passed":passed,
        "decision":decision,
        "selected_stage":selected,
        "rationale":rationale,
        "semantic_rewrite":False,
        "new_answer_generated":False,
    }

def main() -> int:
    out = Path("macro_pc_v10_artifact")
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
    ask_invocations = 0
    ask_resolutions = 0
    ask_abstentions = 0
    unsafe_selections = 0

    for pid in ["p01","p03","p04"]:
        g = generate_case(model,tok,pid)
        verifier = VALIDATORS[pid]
        evals = {}
        vectors = {}
        for stage in STAGES:
            ev = verifier(g["stages"][stage]["text"].strip())
            evals[stage] = ev
            vectors[stage] = v09.vector(ev)

        ap = v09.anti_regression_adjudicate(vectors)
        ask = None
        final_decision = None
        selected_stage = None

        if ap["decision"] == "SELECT":
            final_decision = "SELECT"
            selected_stage = ap["selected_stage"]
        else:
            ask = ask_resolve(ap["frontier"], g["stages"], pid)
            if ask["invoked"]:
                ask_invocations += 1
                if ask["decision"] == "SELECT":
                    ask_resolutions += 1
                    final_decision = "SELECT"
                    selected_stage = ask["selected_stage"]
                else:
                    ask_abstentions += 1
                    final_decision = "ABSTAIN"
            else:
                final_decision = "ABSTAIN"

        if selected_stage is not None:
            # Safety check: never select a source-verifier Pareto-dominated stage.
            sv = vectors[selected_stage]
            if any(v09.dominates(v,sv) for s,v in vectors.items() if s != selected_stage):
                unsafe_selections += 1

        final_text = (
            g["stages"][selected_stage]["text"].strip()
            if selected_stage is not None else None
        )

        record = {
            "schema":"cfl-p-internal-ask-case/v1.0",
            "created_at":utcnow(),
            "prompt_id":pid,
            "regime":g["regime"],
            "source_budget":g["source_budget"],
            "seeds":SEEDS,
            "stages":g["stages"],
            "source_evaluations":evals,
            "source_vectors":vectors,
            "A_P":ap,
            "ASK":ask,
            "P_final":{
                "decision":final_decision,
                "selected_stage":selected_stage,
                "text":final_text,
                "available":selected_stage is not None,
            },
        }
        record["sha256"] = digest(record)
        cases[pid] = record
        (out/f"{pid}_ASK.json").write_text(
            json.dumps(record,indent=2,ensure_ascii=False),encoding="utf-8"
        )

    summary = {
        "schema":"cfl-p-internal-ask-summary/v1.0",
        "created_at":utcnow(),
        "model_id":MODEL_ID,
        "source_notebook":SOURCE_NOTEBOOK,
        "cases":["p01","p03","p04"],
        "external_verifier_frozen_before_execution":True,
        "external_verifier_sources":EXTERNAL_VERIFIER_SOURCES,
        "counts":{
            "executed_cases":3,
            "ASK_invocations":ask_invocations,
            "ASK_unique_resolutions":ask_resolutions,
            "ASK_abstentions":ask_abstentions,
            "unsafe_selections":unsafe_selections,
            "final_single_P_available":sum(1 for x in cases.values() if x["P_final"]["available"]),
        },
        "case_decisions":{
            pid:{
                "A_P":cases[pid]["A_P"]["decision"],
                "frontier":cases[pid]["A_P"]["frontier"],
                "ASK_decision":cases[pid]["ASK"]["decision"] if cases[pid]["ASK"] else None,
                "final_decision":cases[pid]["P_final"]["decision"],
                "selected_stage":cases[pid]["P_final"]["selected_stage"],
            } for pid in cases
        },
        "gate_pass": (
            unsafe_selections == 0
            and ask_invocations >= 1
            and all(
                not (x["ASK"] and x["ASK"]["decision"]=="SELECT" and len(x["ASK"]["passed"])!=1)
                for x in cases.values()
            )
        ),
        "authority_transfer":False,
        "global_macro_prior_changed":False,
    }
    summary["sha256"] = digest(summary)
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")

    zpost = {
        "schema":"cfl-p-internal-ask-zpost/v1.0",
        "created_at":utcnow(),
        "p04":{
            "frontier":cases["p04"]["A_P"]["frontier"],
            "ASK":cases["p04"]["ASK"],
            "final_decision":cases["p04"]["P_final"]["decision"],
        },
        "authority_transfer":False,
        "reading":"Independent verification may reduce uncertainty, but is allowed to preserve abstention when no frontier candidate passes all frozen necessary conditions.",
    }
    zpost["sha256"] = digest(zpost)
    (out/"z_post.json").write_text(json.dumps(zpost,indent=2,ensure_ascii=False),encoding="utf-8")

    head="0"*64
    events=[]
    for pid in ["p01","p03","p04"]:
        for et,payload in [
            ("P_INTERNAL_FRONTIER_FROZEN",{"prompt_id":pid,"frontier":cases[pid]["A_P"]["frontier"],"case_sha256":cases[pid]["sha256"]}),
            ("ASK_OBSERVATION_RECORDED",{"prompt_id":pid,"ASK":cases[pid]["ASK"]}),
            ("P_FINAL_DECISION_FROZEN",{"prompt_id":pid,"P_final":cases[pid]["P_final"]}),
        ]:
            ev={"index":len(events),"event_type":et,"created_at":utcnow(),"payload":payload,"prev_hash":head}
            ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    ev={"index":len(events),"event_type":"ASK_GATE_CLOSED","created_at":utcnow(),
        "payload":{"summary_sha256":summary["sha256"],"gate_pass":summary["gate_pass"],"zpost_sha256":zpost["sha256"]},
        "prev_hash":head}
    ev["hash"]=digest(ev);head=ev["hash"];events.append(ev)
    with (out/"ledger.jsonl").open("w",encoding="utf-8") as f:
        for ev in events:f.write(canonical_json(ev)+"\n")

    manifest={
        "schema":"cfl-p-internal-ask-gate/v1.0",
        "created_at":utcnow(),
        "status":"PASS" if summary["gate_pass"] else "FAIL_WITH_EVIDENCE",
        "model_id":MODEL_ID,
        "real_model_execution":True,
        "synthetic_observations":False,
        "independent_external_verification":True,
        "new_answer_generated_by_ASK":False,
        "unsafe_selections":unsafe_selections,
        "ASK_invocations":ask_invocations,
        "ASK_abstentions":ask_abstentions,
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

    print(json.dumps({"summary":summary,"zpost":zpost,"ledger_head_hash":head},indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
