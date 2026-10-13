#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re

import run_macro_pc_gate_v05 as base

base.BENCHMARK_ID = "CFLDECODER_V2_P01_STRICT_PARAMETRIC_EXTRACTION"
base.SOURCE_PROMPT_ID = "p01"

SOURCE_BUDGET = 96
L3_META_BUDGET = 256

base.PROMPT = r'''Read the following noisy text block exactly once. Extract three specific variables and return them formatted as a rigidly nested JSON object. No output tokens are permitted outside the opening `{` and closing `}` of the JSON structure — no preamble, no trailing commentary, no whitespace beyond standard JSON formatting.

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

def parse_json_object_only(text):
    s = text.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None, False
    try:
        return json.loads(s), True
    except Exception:
        return None, False

def validate_p01(text: str):
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
    return {
        "format_pass": bool(ok),
        "content_pass": bool(content_pass),
        "exact_answer_pass": bool(ok and content_pass),
        "constraint_violations": [] if ok else ["json_object_only"],
        "validator": "recovered_CFLDECODER_V2_p01_semantics",
        "source_budget": SOURCE_BUDGET,
    }

base.validate_p08 = validate_p01

_orig_generate = base.generate

def source_budget_generate(model, tokenizer, *, prompt, system_prompt, seed, processor=None, max_new_tokens=192):
    is_l3 = prompt.startswith("ORIGINAL PROBLEM:")
    if is_l3:
        system_prompt = (
            "You are executing the third and final PROCEDURAL orchestration pass. "
            "The wrapper format for this pass is mandatory: output exactly two sections "
            "<RAW>...</RAW> then <INFORMED>...</INFORMED>. "
            "Inside each section, solve the ORIGINAL PROBLEM. The wrapper tags are orchestration metadata, "
            "not part of the final candidate. The content inside <INFORMED> must itself obey the ORIGINAL "
            "PROBLEM output format exactly. Do not mention any configurational or parallel solver."
        )
        budget = L3_META_BUDGET
    else:
        budget = SOURCE_BUDGET
    return _orig_generate(
        model, tokenizer,
        prompt=prompt,
        system_prompt=system_prompt,
        seed=seed,
        processor=processor,
        max_new_tokens=budget,
    )

base.generate = source_budget_generate

if __name__ == "__main__":
    raise SystemExit(base.main())
