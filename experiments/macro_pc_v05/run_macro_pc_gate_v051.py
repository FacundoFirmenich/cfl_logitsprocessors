#!/usr/bin/env python3
from __future__ import annotations

import re
import run_macro_pc_gate_v05 as base

base.BENCHMARK_ID = "CFLDECODER_V2_P06_FINITE_STATE_MACHINE"
base.SOURCE_PROMPT_ID = "p06"
base.PROMPT = r'''A closed system operates across exactly four states: **IDLE**, **ACTIVE**, **SUSPENDED**, **ERROR**. The transition rules are exhaustive and strictly defined as follows:

- From IDLE: input `START` → ACTIVE; input `FAULT` → ERROR; any other input → IDLE
- From ACTIVE: input `PAUSE` → SUSPENDED; input `FAULT` → ERROR; input `STOP` → IDLE; any other input → ACTIVE
- From SUSPENDED: input `RESUME` → ACTIVE; input `STOP` → IDLE; input `FAULT` → ERROR; any other input → SUSPENDED
- From ERROR: input `RESET` → IDLE; any other input → ERROR

**Initial state:** IDLE

**Input sequence:** `START`, `PAUSE`, `RESUME`, `FAULT`, `RESET`, `START`, `STOP`, `FAULT`, `RESET`, `START`, `PAUSE`, `STOP`

Output a complete state trace as a numbered list. Each entry must follow the exact format:

`Step N: Input=[INPUT] | Prior State=[STATE] → Next State=[STATE]`

No steps may be skipped, merged, or summarized. The trace must cover all 12 inputs.
'''

def expected_trace():
    transitions = {
        "IDLE": {"START": "ACTIVE", "FAULT": "ERROR"},
        "ACTIVE": {"PAUSE": "SUSPENDED", "FAULT": "ERROR", "STOP": "IDLE"},
        "SUSPENDED": {"RESUME": "ACTIVE", "STOP": "IDLE", "FAULT": "ERROR"},
        "ERROR": {"RESET": "IDLE"},
    }
    seq = ["START","PAUSE","RESUME","FAULT","RESET","START","STOP","FAULT","RESET","START","PAUSE","STOP"]
    state = "IDLE"
    out = []
    for i, inp in enumerate(seq, 1):
        prior = state
        state = transitions.get(state, {}).get(inp, state)
        out.append((i, inp, prior, state))
    return out

EXPECTED = expected_trace()

def validate_p06(text: str):
    t = text.strip()
    lines = [l for l in t.splitlines() if l.strip().lower().startswith("step")]
    format_pass = len(lines) == 12
    content_pass = True
    misses = []
    for i, inp, prior, nxt in EXPECTED:
        pat = rf"Step\s+{i}\s*:\s*Input=\[{inp}\]\s*\|\s*Prior State=\[{prior}\]\s*[→\-]+\s*Next State=\[{nxt}\]"
        if not re.search(pat, t):
            content_pass = False
            misses.append(i)
    return {
        "format_pass": format_pass,
        "content_pass": content_pass,
        "exact_answer_pass": bool(format_pass and content_pass),
        "missing_or_mismatched_steps": misses,
        "validator": "recovered_CFLDECODER_V2_p06_semantics",
    }

base.validate_p08 = validate_p06

if __name__ == "__main__":
    raise SystemExit(base.main())
