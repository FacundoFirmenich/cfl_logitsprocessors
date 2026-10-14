#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, tempfile, zipfile, shutil
from pathlib import Path
from jsonschema import Draft202012Validator

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input",type=Path)
    p.add_argument("--schema",type=Path,required=True)
    a=p.parse_args()
    cleanup=None
    root=a.input
    if a.input.is_file():
        cleanup=Path(tempfile.mkdtemp(prefix="qas_p2_result_"))
        with zipfile.ZipFile(a.input) as z:
            bad=z.testzip()
            if bad: raise SystemExit(f"corrupt ZIP member: {bad}")
            z.extractall(cleanup)
        root=cleanup

    required=[
        "qas_p2_evidence_receipts.jsonl",
        "qas_p2_universal_top64_test.json",
        "qas_p2_receipt_manifest.json",
        "run_manifest.json",
        "SHA256SUMS.txt",
        "campaign.sqlite",
    ]
    for name in required:
        if not (root/name).exists():
            raise SystemExit(f"missing required result: {name}")

    schema=json.loads(a.schema.read_text())
    v=Draft202012Validator(schema)
    receipts=[]
    for n,line in enumerate((root/"qas_p2_evidence_receipts.jsonl").read_text().splitlines(),1):
        if not line.strip(): continue
        r=json.loads(line)
        errors=list(v.iter_errors(r))
        if errors: raise SystemExit(f"receipt line {n}: {errors[0].message}")
        if len(r["baseline_top64_ids"])!=len(r["baseline_top64_probs"]):
            raise SystemExit(f"receipt line {n}: candidate ID/prob mismatch")
        if r["support_size"]!=len(r["support_ids"]):
            raise SystemExit(f"receipt line {n}: support size mismatch")
        support_hash=hashlib.sha256(
            json.dumps(sorted(r["support_ids"]),separators=(",",":")).encode()
        ).hexdigest()
        if support_hash!=r["support_hash"]:
            raise SystemExit(f"receipt line {n}: support hash mismatch")
        receipts.append(r)

    test=json.loads((root/"qas_p2_universal_top64_test.json").read_text())
    violations=sum(
        bool(set(r["support_ids"])-set(r["baseline_top64_ids"]))
        for r in receipts
    )
    if violations!=test["violation_count"]:
        raise SystemExit("top-64 violation count mismatch")
    expected="FALSIFIED" if violations else "PASSED_FROZEN_CAMPAIGN"
    if test["status"]!=expected:
        raise SystemExit("top-64 frozen test status mismatch")

    manifest=json.loads((root/"qas_p2_receipt_manifest.json").read_text())
    if manifest["receipt_count"]!=len(receipts):
        raise SystemExit("receipt manifest count mismatch")
    if manifest["receipt_file_sha256"]!=sha(root/"qas_p2_evidence_receipts.jsonl"):
        raise SystemExit("receipt file hash mismatch")
    if manifest["top64_test_sha256"]!=sha(root/"qas_p2_universal_top64_test.json"):
        raise SystemExit("top64 test hash mismatch")

    result={
        "status":"PASS",
        "receipt_count":len(receipts),
        "top64_violation_count":violations,
        "top64_status":test["status"],
        "result_root":str(root),
    }
    print(json.dumps(result,indent=2))
    if cleanup: shutil.rmtree(cleanup)

if __name__=="__main__":
    main()
