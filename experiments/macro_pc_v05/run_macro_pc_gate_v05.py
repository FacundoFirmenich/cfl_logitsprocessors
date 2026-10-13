#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import platform
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, LogitsProcessor, LogitsProcessorList, set_seed
import transformers

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
BENCHMARK_ID = "CFLDECODER_V2_P08_CAUSAL_NOISE_DETECTION"
SOURCE_NOTEBOOK = "CFLDECODER_V2_p01_p10_constraints_sequence.ipynb"
SOURCE_PROMPT_ID = "p08"
SEEDS = {"L1": 101, "L2": 202, "L3": 303, "C": 404}

PROMPT = r'''Evaluate the following five-step reasoning chain. Exactly one step contains a structural inference fallacy — a logical error embedded in the inferential move itself, not a factual error about the world. Identify the single failing step, name the specific fallacy present, and provide a one-sentence demonstration of why that inferential move is structurally invalid. Do not critique any other step.

**Reasoning chain:**

1. All systems that undergo rapid entropy increase exhibit measurable temperature rise.
2. System X exhibits a measurable temperature rise.
3. Therefore, System X is undergoing rapid entropy increase.
4. Because System X is undergoing rapid entropy increase, and all systems undergoing rapid entropy increase are approaching thermodynamic equilibrium, System X must currently be at the global temperature maximum for its operational cycle.
5. Therefore, safety protocols requiring intervention above the global temperature maximum are now triggered.

Output format — three labeled fields, nothing else:

FAILING STEP: [number]
FALLACY: [name of the fallacy]
DEMONSTRATION: [one sentence]
'''

SYSTEM_P = (
    "Solve the complete problem carefully. Preserve uncertainty, distinguish facts from inferences, "
    "and do not refer to any parallel solver. Obey the requested output format exactly."
)
SYSTEM_C = (
    "Solve the complete problem independently. Explore non-dominant and tail-supported possibilities, "
    "but state uncertainty and do not refer to any procedural/left-side answer. Obey the requested output format exactly."
)


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    raw = obj if isinstance(obj, (bytes, bytearray)) else canonical_json(obj).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class TALMMassRightSoftConfig:
    tail_fraction: float = 0.08
    left_weight: float = 0.2
    right_weight: float = 0.8
    left_boost: float = 0.08
    right_boost: float = 0.28
    min_tail_tokens: int = 8
    max_tail_tokens: int = 4096
    robust_scale_epsilon: float = 1e-6
    mass_tail_fraction: float = 0.025
    diagnostics_every_n_steps: int = 16

    def __post_init__(self) -> None:
        if not math.isclose(self.left_weight + self.right_weight, 1.0, abs_tol=1e-12):
            raise ValueError("TALM side weights must sum to one")


class TALMMassRightSoftProcessor(LogitsProcessor):
    """Exact specialization of the TALM v0.5.2 mass-right-soft branch.

    This is not a new operator: it is the v0.5.2 mass-selection and robust-linear
    weighting path specialized to the frozen mass-right-soft configuration used by
    the prior CFL shadow producer.
    """

    def __init__(self, config: TALMMassRightSoftConfig):
        self.config = config
        self.step_index = 0
        self.diagnostics: list[dict[str, Any]] = []

    @staticmethod
    def _safe_probs(x: torch.Tensor) -> torch.Tensor:
        x64 = x.detach().to(torch.float64)
        finite = torch.isfinite(x64)
        if not bool(finite.any()):
            return torch.full_like(x64, 1.0 / max(1, x64.numel()))
        min_f = torch.min(x64[finite])
        safe = torch.where(finite, x64, min_f - 1000.0)
        p = torch.softmax(safe, dim=-1)
        p = torch.nan_to_num(p, nan=0.0, posinf=0.0, neginf=0.0)
        s = p.sum()
        return p / s if float(s) > 0 else torch.full_like(x64, 1.0 / max(1, x64.numel()))

    def _take_by_mass(self, probs: torch.Tensor, order: torch.Tensor, target: float) -> tuple[torch.Tensor, int]:
        if target <= 0:
            return torch.empty(0, dtype=torch.long, device=order.device), 0
        cum = torch.cumsum(probs[order], dim=0)
        raw = int(torch.searchsorted(cum, torch.tensor(target, dtype=cum.dtype, device=cum.device)).item() + 1)
        raw = min(raw, int(order.numel()))
        count = max(self.config.min_tail_tokens, raw)
        count = min(count, self.config.max_tail_tokens, int(order.numel()))
        return order[:count], raw

    def _process_one(self, scores: torch.Tensor) -> torch.Tensor:
        cfg = self.config
        original = scores
        x = scores.clone()
        finite_mask = torch.isfinite(x)
        if not bool(finite_mask.any()):
            self.step_index += 1
            return x
        finite_vals = x[finite_mask]
        _, local_idx = torch.sort(finite_vals, stable=True)
        finite_indices = torch.nonzero(finite_mask, as_tuple=False).flatten()
        sorted_low = finite_indices[local_idx]
        probs = self._safe_probs(original)
        sorted_high = torch.argsort(probs, descending=True)
        left_idx, raw_left = self._take_by_mass(probs, sorted_low, cfg.mass_tail_fraction * cfg.left_weight)
        right_idx, raw_right = self._take_by_mass(probs, sorted_high, cfg.mass_tail_fraction * cfg.right_weight)

        median = torch.median(finite_vals)
        mad = torch.median(torch.abs(finite_vals - median))
        scale = 1.4826 * mad + cfg.robust_scale_epsilon

        def robust_weights(vals: torch.Tensor, boost: float) -> torch.Tensor:
            if vals.numel() == 0 or boost == 0.0:
                return torch.zeros_like(vals)
            z = torch.abs((vals - median) / torch.clamp(scale, min=cfg.robust_scale_epsilon))
            z = z / torch.clamp(torch.max(z), min=cfg.robust_scale_epsilon)
            return boost * z.to(vals.dtype)

        if left_idx.numel():
            x[left_idx] = x[left_idx] + robust_weights(x[left_idx], cfg.left_boost)
        if right_idx.numel():
            x[right_idx] = x[right_idx] + robust_weights(x[right_idx], cfg.right_boost)

        if self.step_index % cfg.diagnostics_every_n_steps == 0:
            p1 = self._safe_probs(x)
            selected = torch.unique(torch.cat([left_idx, right_idx]))
            self.diagnostics.append({
                "step_index": self.step_index,
                "selection_mode": "mass",
                "left_tail_count": int(left_idx.numel()),
                "right_tail_count": int(right_idx.numel()),
                "raw_left_tail_count": int(raw_left),
                "raw_right_tail_count": int(raw_right),
                "top1_changed": int(torch.argmax(probs).item() != torch.argmax(p1).item()),
                "total_variation_distance": float((0.5 * torch.abs(probs - p1).sum()).item()),
                "original_selected_tail_mass": float(probs[selected].sum().item()) if selected.numel() else 0.0,
                "modulated_selected_tail_mass": float(p1[selected].sum().item()) if selected.numel() else 0.0,
            })
        self.step_index += 1
        return x

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        if scores.ndim == 1:
            return self._process_one(scores)
        out = scores.clone()
        for b in range(out.shape[0]):
            out[b] = self._process_one(out[b])
        return out


def format_prompt(tokenizer, prompt: str, system_prompt: str) -> str:
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
    return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)


def generate(model, tokenizer, *, prompt: str, system_prompt: str, seed: int, processor=None, max_new_tokens: int = 192) -> dict[str, Any]:
    set_seed(seed)
    formatted = format_prompt(tokenizer, prompt, system_prompt)
    inputs = tokenizer(formatted, return_tensors="pt")
    kwargs: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": True,
        "temperature": 0.8,
        "top_p": 0.9,
        "pad_token_id": tokenizer.pad_token_id,
        "eos_token_id": tokenizer.eos_token_id,
    }
    if processor is not None:
        kwargs["logits_processor"] = LogitsProcessorList([processor])
    with torch.inference_mode():
        output = model.generate(**inputs, **kwargs)
    prompt_len = int(inputs["input_ids"].shape[-1])
    ids = [int(v) for v in output[0, prompt_len:].tolist()]
    text = tokenizer.decode(ids, skip_special_tokens=True)
    return {
        "seed": seed,
        "text": text,
        "token_ids": ids,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "formatted_prompt_sha256": hashlib.sha256(formatted.encode()).hexdigest(),
        "output_sha256": digest({"seed": seed, "text": text, "token_ids": ids}),
    }


def l3_prompt(problem: str, l1: str, l2: str) -> str:
    return (
        "ORIGINAL PROBLEM:\n" + problem + "\n\n"
        "INDEPENDENT PROCEDURAL ATTEMPT L1:\n" + l1 + "\n\n"
        "INDEPENDENT PROCEDURAL ATTEMPT L2:\n" + l2 + "\n\n"
        "Produce two clearly delimited sections. First write <RAW>...</RAW>: solve the original problem anew. "
        "Then write <INFORMED>...</INFORMED>: provide the final enriched resolution after checking the raw answer "
        "against L1 and L2. Inside <INFORMED>, obey the ORIGINAL PROBLEM output format exactly and include no other fields."
    )


def extract_informed(text: str) -> str:
    m = re.search(r"<INFORMED>(.*?)</INFORMED>", text, flags=re.S | re.I)
    return m.group(1).strip() if m else text.strip()


def validate_p08(text: str) -> dict[str, Any]:
    """Recovered CFL Decoder p08 exact-content validator semantics."""
    t = text.strip()
    low = t.lower()
    format_pass = all(label in t for label in ["FAILING STEP:", "FALLACY:", "DEMONSTRATION:"])
    content_pass = bool(re.search(r"FAILING STEP:\s*3\b", t)) and any(
        x in low for x in ["affirming the consequent", "converse error", "converse fallacy"]
    )
    return {
        "format_pass": format_pass,
        "content_pass": content_pass,
        "exact_answer_pass": bool(format_pass and content_pass),
        "validator": "recovered_CFLDECODER_V2_p08_semantics",
    }


def dirichlet_after(label: str) -> dict[str, float]:
    a = {"BENEFIT": 1.0, "NEUTRAL": 1.0, "HARM": 1.0}
    a[label] += 1.0
    s = sum(a.values())
    return {"alpha_benefit": a["BENEFIT"], "alpha_neutral": a["NEUTRAL"], "alpha_harm": a["HARM"],
            "p_benefit": a["BENEFIT"]/s, "p_neutral": a["NEUTRAL"]/s, "p_harm": a["HARM"]/s}


def label_from_exact(result: dict[str, Any]) -> str:
    return "BENEFIT" if result["exact_answer_pass"] else "HARM"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="macro_pc_v05_artifact")
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    torch.set_num_threads(max(1, min(4, os.cpu_count() or 1)))
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype=torch.float32, low_cpu_mem_usage=True)
    model.eval()

    l1 = generate(model, tokenizer, prompt=PROMPT, system_prompt=SYSTEM_P, seed=SEEDS["L1"])
    l2 = generate(model, tokenizer, prompt=PROMPT, system_prompt=SYSTEM_P, seed=SEEDS["L2"])
    l3 = generate(model, tokenizer, prompt=l3_prompt(PROMPT, l1["text"], l2["text"]), system_prompt=SYSTEM_P, seed=SEEDS["L3"])
    p_final = extract_informed(l3["text"])

    talm_cfg = TALMMassRightSoftConfig()
    processor = TALMMassRightSoftProcessor(talm_cfg)
    c_run = generate(model, tokenizer, prompt=PROMPT, system_prompt=SYSTEM_C, seed=SEEDS["C"], processor=processor)
    c_final = c_run["text"].strip()

    candidates = {
        "schema": "cfl-macro-pc-candidates/v0.5",
        "created_at": utcnow(),
        "benchmark_id": BENCHMARK_ID,
        "source_notebook": SOURCE_NOTEBOOK,
        "source_prompt_id": SOURCE_PROMPT_ID,
        "model_id": MODEL_ID,
        "problem": PROMPT,
        "P": {"final_text": p_final, "L1": l1, "L2": l2, "L3": l3},
        "C": {"final_text": c_final, "carrier": "talm_mass_right_soft", "run": c_run,
              "talm_config": asdict(talm_cfg), "talm_diagnostics": processor.diagnostics},
    }
    p_hash = digest(candidates["P"])
    c_hash = digest(candidates["C"])
    freeze_hash = digest({"P": p_hash, "C": c_hash, "benchmark_id": BENCHMARK_ID})
    candidates["candidate_hashes"] = {"P": p_hash, "C": c_hash, "freeze": freeze_hash}
    (out / "candidates.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    decision = {
        "schema": "cfl-macro-pc-decision/v0.5",
        "created_at": utcnow(),
        "candidate_freeze_hash": freeze_hash,
        "decision": "BASELINE",
        "authority_transfer": False,
        "rationale": [
            "macro P/C jurisdiction model is still warmup/untrained",
            "exact benchmark outcome intentionally withheld until after decision freeze",
            "no process may receive authority from one uncalibrated case",
        ],
        "posterior_before": {
            "P": {"alpha": [1.0, 1.0, 1.0]},
            "C": {"alpha": [1.0, 1.0, 1.0]},
        },
    }
    decision["decision_sha256"] = digest(decision)
    (out / "decision_frozen.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")

    p_eval = validate_p08(p_final)
    c_eval = validate_p08(c_final)
    outcome = {
        "schema": "cfl-macro-pc-outcome/v0.5",
        "created_at": utcnow(),
        "decision_sha256_before_outcome": decision["decision_sha256"],
        "candidate_freeze_hash": freeze_hash,
        "validator_source": f"{SOURCE_NOTEBOOK}:{SOURCE_PROMPT_ID}",
        "P": p_eval,
        "C": c_eval,
    }
    outcome["outcome_sha256"] = digest(outcome)
    (out / "outcome_exact.json").write_text(json.dumps(outcome, indent=2), encoding="utf-8")

    p_label = label_from_exact(p_eval)
    c_label = label_from_exact(c_eval)
    successor = {
        "schema": "cfl-macro-pc-successor/v0.5",
        "created_at": utcnow(),
        "source_model_version": 0,
        "successor_model_version": 1,
        "source_decision_sha256": decision["decision_sha256"],
        "source_outcome_sha256": outcome["outcome_sha256"],
        "future_only": True,
        "historical_decision_mutated": False,
        "namespace": "MACRO_P_C_AUTHORITY",
        "P": {"label": p_label, "posterior": dirichlet_after(p_label)},
        "C": {"label": c_label, "posterior": dirichlet_after(c_label)},
        "authority_status": "SHADOW_MACRO_PC_WARMUP",
        "authority_transfer": False,
        "note": "One exact benchmark outcome initializes a future-only macro posterior; it is insufficient for operational authority.",
    }
    successor["successor_sha256"] = digest(successor)
    (out / "successor_model_v1.json").write_text(json.dumps(successor, indent=2), encoding="utf-8")

    ledger_events = []
    head = "0" * 64
    for event_type, payload in [
        ("SESSION_OPENED", {"benchmark_id": BENCHMARK_ID, "model_id": MODEL_ID}),
        ("CANDIDATES_FROZEN", {"freeze_hash": freeze_hash, "P": p_hash, "C": c_hash}),
        ("DECISION_FROZEN", {"decision_sha256": decision["decision_sha256"], "decision": decision["decision"]}),
        ("OUTCOME_RECORDED", {"outcome_sha256": outcome["outcome_sha256"], "P_pass": p_eval["exact_answer_pass"], "C_pass": c_eval["exact_answer_pass"]}),
        ("SUCCESSOR_RELEASED", {"successor_sha256": successor["successor_sha256"], "version": 1}),
    ]:
        ev = {"index": len(ledger_events), "event_type": event_type, "created_at": utcnow(), "payload": payload, "prev_hash": head}
        ev["hash"] = digest(ev)
        head = ev["hash"]
        ledger_events.append(ev)
    with (out / "ledger.jsonl").open("w", encoding="utf-8") as f:
        for ev in ledger_events:
            f.write(canonical_json(ev) + "\n")

    manifest = {
        "schema": "cfl-macro-pc-gate/v0.5",
        "created_at": utcnow(),
        "status": "SUCCESSOR_RELEASED_SHADOW_ONLY",
        "benchmark_id": BENCHMARK_ID,
        "source_prompt_id": SOURCE_PROMPT_ID,
        "source_notebook": SOURCE_NOTEBOOK,
        "model_id": MODEL_ID,
        "seeds": SEEDS,
        "candidate_freeze_hash": freeze_hash,
        "decision_sha256": decision["decision_sha256"],
        "outcome_sha256": outcome["outcome_sha256"],
        "successor_sha256": successor["successor_sha256"],
        "ledger_head_hash": head,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "claims_boundary": {
            "real_model_execution": True,
            "real_TALM_execution": True,
            "exact_deterministic_outcome": True,
            "future_only_macro_update": True,
            "operational_authority": False,
            "z_star_executed": False,
            "single_case_only": True,
        },
    }
    for fn in ["candidates.json", "decision_frozen.json", "outcome_exact.json", "successor_model_v1.json", "ledger.jsonl"]:
        manifest.setdefault("files", {})[fn] = hashlib.sha256((out / fn).read_bytes()).hexdigest()
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    assert outcome["decision_sha256_before_outcome"] == decision["decision_sha256"]
    assert successor["source_decision_sha256"] == decision["decision_sha256"]
    assert successor["source_outcome_sha256"] == outcome["outcome_sha256"]
    assert successor["historical_decision_mutated"] is False

    summary = {
        "benchmark_id": BENCHMARK_ID,
        "model_id": MODEL_ID,
        "candidate_freeze_hash": freeze_hash,
        "decision": decision["decision"],
        "P_exact_pass": p_eval["exact_answer_pass"],
        "C_exact_pass": c_eval["exact_answer_pass"],
        "P_label": p_label,
        "C_label": c_label,
        "successor_version": 1,
        "successor_sha256": successor["successor_sha256"],
        "ledger_head_hash": head,
        "output_dir": str(out),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
