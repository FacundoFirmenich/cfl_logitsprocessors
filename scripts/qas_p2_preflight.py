#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, hashlib, json, re, zipfile, io
from pathlib import Path

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fail(msg: str):
    raise SystemExit("PRECHECK_FAIL: " + msg)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo-root",type=Path,default=Path("."))
    a=p.parse_args()
    root=a.repo_root.resolve()
    nbp=root/"notebooks/RDS_V3_8_QAS_P2_LABEL_COMPLETE_QWEN35_4B_COLAB_GPU.ipynb"
    freeze_p=root/"execution/qas_p2/GPU_EXECUTION_FREEZE.json"
    schema_p=root/"execution/qas_p2/qas_p2_receipt_schema.json"
    prospect_p=root/"execution/qas_p2/QAS_P2_PROSPECTIVE_FREEZE.json"
    for x in (nbp,freeze_p,schema_p,prospect_p):
        if not x.exists(): fail(f"missing {x}")

    nb=json.loads(nbp.read_text(encoding="utf-8"))
    freeze=json.loads(freeze_p.read_text())
    schema=json.loads(schema_p.read_text())
    prospect=json.loads(prospect_p.read_text())
    source="\n".join("".join(c.get("source",[])) for c in nb["cells"])

    if any(c.get("outputs") for c in nb["cells"] if c["cell_type"]=="code"):
        fail("portable notebook contains saved execution outputs")
    required=[
        'MODEL_ID = "Qwen/Qwen3.5-4B"',
        'MODEL_REVISION_REQUESTED = "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"',
        '"record_coordinate_labels": True',
        '"baseline_candidate_topk": 64',
        '"schema": "qas.p2.evidence.v1"',
        'qas_p2_evidence_receipts.jsonl',
        'qas_p2_universal_top64_test.json',
        'QAS_P2_WORK_ROOT',
    ]
    for token in required:
        if token not in source: fail(f"notebook missing invariant: {token}")
    forbidden=["/kaggle/working","kaggle_secrets"]
    for token in forbidden:
        if token in source: fail(f"Colab notebook still contains Kaggle-only dependency: {token}")

    m=re.search(r"EMBEDDED_RUNTIME_HEX\s*=\s*'([0-9a-fA-F]+)'",source)
    if not m: fail("embedded runtime hex not found")
    runtime=bytes.fromhex(m.group(1))
    runtime_sha=hashlib.sha256(runtime).hexdigest()
    if runtime_sha!=freeze["embedded_runtime_zip_sha256"]:
        fail(f"runtime hash mismatch {runtime_sha}")
    with zipfile.ZipFile(io.BytesIO(runtime)) as z:
        if z.testzip() is not None: fail("embedded runtime ZIP corrupt")
        names=set(z.namelist())
        expected={"RUNTIME_INFO.json","RUNTIME_MANIFEST.json","rds_v35/rds_core.py","rds_v35/verifiers.py","tests/test_runtime.py"}
        if not expected.issubset(names): fail("embedded runtime incomplete")
        for name in names:
            if name.endswith(".py"):
                ast.parse(z.read(name).decode("utf-8"),filename=name)

    if schema.get("properties",{}).get("schema",{}).get("const")!="qas.p2.evidence.v1":
        fail("receipt schema const mismatch")
    if prospect.get("status")!="FROZEN_DESIGN_NOT_EXECUTED":
        fail("prospective freeze status mutated")
    if freeze.get("status")!="EXECUTION_READY_NOT_EXECUTED":
        fail("execution freeze status mutated")
    if freeze["portable_colab_notebook_sha256"]!=sha(nbp):
        fail("portable notebook hash mismatch")
    if freeze["receipt_schema_sha256"]!=sha(schema_p):
        fail("receipt schema hash mismatch")
    if freeze["prospective_freeze_sha256"]!=sha(prospect_p):
        fail("prospective freeze hash mismatch")

    report={
        "status":"PASS",
        "notebook_sha256":sha(nbp),
        "embedded_runtime_sha256":runtime_sha,
        "receipt_schema_sha256":sha(schema_p),
        "prospective_freeze_sha256":sha(prospect_p),
        "saved_outputs":False,
        "gpu_executed":False,
    }
    out=root/"execution/qas_p2/PREFLIGHT_RESULT.json"
    out.write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
