#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

MODEL_REPO = "convaiinnovations/laya"
MODEL_SUBFOLDER = "typed-decisions"
EXPERIMENT_ID = "LAYA_RDSS_HEADROOM_QWEN35_V0_1"
EPS_GRID = [0.0, 0.5, 1.0]
TRIGGER_FRACTIONS = [0.10, 0.20, 0.30, 0.50]
BANNED_STATE_KEYS = {
    "evaluation_only", "headroom", "oracle_utility", "oracle_method",
    "default_utility", "winner", "review_utility", "human_eval",
}

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def load_jsonl(path: Path):
    rows=[]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows

def state_for(record: dict, ablation: str) -> dict:
    meta = {
        "task_type": record["task_type"],
        "strict_contract": bool(record["strict_contract"]),
        "token_budget": int(record["token_budget"]),
        "frozen_default": "D0",
        "candidate_identity_note": "Candidate labels are opaque; D0 is the frozen default and C1-C5 are alternatives.",
    }
    if ablation == "prompt_only":
        state = {**meta, "prompt": record["prompt_text"]}
    elif ablation == "mechanics_only":
        state = {**meta, "counterfactual_mechanics": record["mechanical_fingerprints"]}
    elif ablation == "prompt_plus_mechanics":
        state = {**meta, "counterfactual_mechanics": record["mechanical_fingerprints"], "prompt": record["prompt_text"]}
    else:
        raise ValueError(ablation)
    raw = canonical_json(state)
    low = raw.lower()
    for key in BANNED_STATE_KEYS:
        if f'"{key.lower()}"' in low:
            raise RuntimeError(f"Leakage firewall tripped on key: {key}")
    return state

def questions(choice_order="forward") -> dict:
    crit = [
        ("DEFAULT_SUFFICIENT", "The frozen default D0 is adequately supported; no material rescue is indicated."),
        ("RESCUE_WORTH_TESTING", "At least one non-default candidate is worth testing because D0 may be materially insufficient."),
        ("ABSTAIN_UNCERTAIN", "The ex-ante state is insufficient to support either default sufficiency or a rescue conclusion."),
    ]
    if choice_order == "reverse":
        crit = list(reversed(crit))
    return {
        "default_insufficient": {
            "type": "noul",
            "instructions": (
                "Given only this ex-ante state, is the frozen default D0 materially insufficient, "
                "such that some non-default authority could plausibly produce a meaningfully better outcome?"
            ),
        },
        "default_sufficient": {
            "type": "noul",
            "instructions": (
                "Given only this ex-ante state, is the frozen default D0 materially sufficient, "
                "with no material evidence that another authority would improve the outcome?"
            ),
        },
        "authority_status": {
            "type": "choice",
            "instructions": "Which authority status is best supported by this ex-ante state?",
            "criteria": dict(crit),
        },
        "continuation_value": {
            "type": "score",
            "instructions": (
                "How strong is the evidence that buying additional computation or counterfactual evaluation "
                "could materially change which authority should be used?"
            ),
            "criteria": [
                "No meaningful evidence.",
                "Weak evidence.",
                "Moderate evidence.",
                "Strong evidence.",
                "Very strong evidence.",
            ],
        },
    }

def get_noul(answer: dict) -> float:
    if "noul" in answer:
        return float(answer["noul"])
    probs = answer.get("probabilities") or answer.get("distribution") or {}
    for k in ("true", "True", "yes", "YES", "1"):
        if k in probs:
            return float(probs[k])
    raise KeyError(f"Cannot extract noul probability: {answer}")

def get_choice_probs(answer: dict) -> dict:
    probs = answer.get("probabilities") or answer.get("distribution") or answer.get("probs")
    if isinstance(probs, dict):
        return {str(k): float(v) for k,v in probs.items()}
    return {}

def binary_metrics(y, p):
    y=np.asarray(y,float)
    p=np.clip(np.asarray(p,float),1e-8,1-1e-8)
    brier=float(np.mean((p-y)**2))
    nll=float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)))
    pos=np.where(y==1)[0]
    neg=np.where(y==0)[0]
    if len(pos) and len(neg):
        wins=ties=0
        for i in pos:
            for j in neg:
                if p[i]>p[j]:
                    wins+=1
                elif p[i]==p[j]:
                    ties+=1
        auc=(wins+0.5*ties)/(len(pos)*len(neg))
    else:
        auc=float("nan")
    return {"brier":brier,"nll":nll,"auc":float(auc)}

def ranking_metrics(headroom, score):
    h=np.asarray(headroom,float)
    s=np.asarray(score,float)
    order=np.argsort(-s, kind="mergesort")
    total=float(h.sum())
    n=len(h)
    out={}
    recalls=[]
    fracs=[]
    cum=0.0
    for rank,idx in enumerate(order,1):
        cum += h[idx]
        fracs.append(rank/n)
        recalls.append(cum/total if total>0 else 0.0)
    auc_curve=float(np.trapezoid(np.r_[0.0,recalls], np.r_[0.0,fracs]))
    out["HCI"] = 2*auc_curve-1
    out["headroom_total"] = total
    for q in TRIGGER_FRACTIONS:
        k=max(1,int(math.ceil(q*n)))
        idx=order[:k]
        captured=float(h[idx].sum())
        out[f"top_{int(q*100)}_k"] = k
        out[f"top_{int(q*100)}_headroom_recall"] = captured/total if total>0 else 0.0
        out[f"top_{int(q*100)}_headroom_density"] = float(h[idx].mean())
    return out

def choice_tv(a,b):
    keys=sorted(set(a)|set(b))
    if not keys:
        return float("nan")
    return 0.5*sum(abs(a.get(k,0.0)-b.get(k,0.0)) for k in keys)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--batch-size",type=int,default=3)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)

    records=load_jsonl(args.data)
    import laya
    t0=time.time()
    agent=laya.load(MODEL_REPO, subfolder=MODEL_SUBFOLDER)
    load_seconds=time.time()-t0

    raw_receipts=[]
    all_pred=[]
    for ablation in ["prompt_only","mechanics_only","prompt_plus_mechanics"]:
        states=[state_for(r,ablation) for r in records]
        state_hashes=[sha256_bytes(canonical_json(s).encode()) for s in states]
        t=time.time()
        fwd=agent.predict_batch(states, questions("forward"), batch_size=args.batch_size, sort_by_length=True)
        fwd_seconds=time.time()-t
        t=time.time()
        rev=agent.predict_batch(states, questions("reverse"), batch_size=args.batch_size, sort_by_length=True)
        rev_seconds=time.time()-t
        for rec,sh,rf,rr in zip(records,state_hashes,fwd,rev):
            af=rf["answers"]
            ar=rr["answers"]
            p_ins=get_noul(af["default_insufficient"])
            p_suf=get_noul(af["default_sufficient"])
            pf=get_choice_probs(af["authority_status"])
            pr=get_choice_probs(ar["authority_status"])
            row={
                "case_id":rec["case_id"],
                "prompt_id":rec["prompt_id"],
                "ablation":ablation,
                "state_sha256":sh,
                "p_default_insufficient":p_ins,
                "p_default_sufficient":p_suf,
                "noul_complement_error":abs(p_ins+p_suf-1.0),
                "choice_order_tv":choice_tv(pf,pr),
                "choice_forward":af["authority_status"].get("choice"),
                "choice_reverse":ar["authority_status"].get("choice"),
                "choice_forward_probabilities":json.dumps(pf,sort_keys=True),
                "choice_reverse_probabilities":json.dumps(pr,sort_keys=True),
                "answer_confidence":af["authority_status"].get("answer_confidence",af["authority_status"].get("confidence")),
                "continuation_score":af["continuation_value"].get("score"),
                "headroom":rec["evaluation_only"]["headroom"],
                "default_utility":rec["evaluation_only"]["default_utility"],
                "oracle_utility":rec["evaluation_only"]["oracle_utility"],
                "router_probability_vs_baseline":rec["internal_exante_comparators"]["router_probability_vs_baseline"],
                "router_max_alt_score_minus_D0":rec["internal_exante_comparators"]["max_alt_score_minus_D0"],
            }
            all_pred.append(row)
            raw_receipts.append({
                "case_id":rec["case_id"],
                "ablation":ablation,
                "state_sha256":sh,
                "forward":rf,
                "reverse":rr,
            })
        (args.out/f"timing_{ablation}.json").write_text(json.dumps({
            "forward_seconds":fwd_seconds,
            "reverse_seconds":rev_seconds,
            "n_cases":len(states)
        },indent=2),encoding="utf-8")

    pred=pd.DataFrame(all_pred)
    pred.to_csv(args.out/"predictions.csv",index=False)
    with (args.out/"raw_receipts.jsonl").open("w",encoding="utf-8") as f:
        for r in raw_receipts:
            f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+"
")

    metrics=[]
    for abl,g in pred.groupby("ablation"):
        score=g.p_default_insufficient.to_numpy(float)
        head=g.headroom.to_numpy(float)
        base={"ablation":abl,"sensor":"laya_noul"}
        coherence={
            "mean_noul_complement_error":float(g.noul_complement_error.mean()),
            "mean_choice_order_tv":float(g.choice_order_tv.dropna().mean()) if g.choice_order_tv.notna().any() else float("nan"),
            "choice_flip_rate":float((g.choice_forward!=g.choice_reverse).mean()),
        }
        for eps in EPS_GRID:
            mat=np.where(head>eps,head,0.0)
            y=(head>eps).astype(int)
            metrics.append({
                **base,
                "epsilon":eps,
                "n":len(g),
                "positives":int(y.sum()),
                **binary_metrics(y,score),
                **ranking_metrics(mat,score),
                **coherence
            })

    g=pred[pred.ablation=="mechanics_only"].copy()
    for sensor,col in [
        ("internal_router_probability_vs_baseline","router_probability_vs_baseline"),
        ("internal_max_alt_score_minus_D0","router_max_alt_score_minus_D0"),
    ]:
        score=g[col].to_numpy(float)
        head=g.headroom.to_numpy(float)
        for eps in EPS_GRID:
            mat=np.where(head>eps,head,0.0)
            y=(head>eps).astype(int)
            if sensor.endswith("probability_vs_baseline"):
                bm = binary_metrics(y, np.clip(score,1e-6,1-1e-6))
            else:
                bm = {"brier":float("nan"),"nll":float("nan"),"auc":binary_metrics(y,1/(1+np.exp(-score)))["auc"]}
            metrics.append({
                "ablation":"internal_exante",
                "sensor":sensor,
                "epsilon":eps,
                "n":len(g),
                "positives":int(y.sum()),
                **bm,
                **ranking_metrics(mat,score)
            })

    metrics_df=pd.DataFrame(metrics)
    metrics_df.to_csv(args.out/"metrics.csv",index=False)
    summary={
        "experiment_id":EXPERIMENT_ID,
        "model_repo":MODEL_REPO,
        "model_subfolder":MODEL_SUBFOLDER,
        "laya_version":getattr(laya,"__version__","unknown"),
        "python":sys.version,
        "platform":platform.platform(),
        "n_cases":len(records),
        "model_load_seconds":load_seconds,
        "data_sha256":sha256_bytes(args.data.read_bytes()),
        "claim_boundary":(
            "Retrospective sensor replay on a closed Qwen3.5 campaign. Laya receives only ex-ante prompt/mechanical state; "
            "human utilities are evaluation-only. This does not establish prospective routing superiority or execution authority."
        ),
        "primary_metric":"low-trigger material headroom concentration (HCI and top-q headroom recall)",
    }
    (args.out/"SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(summary,indent=2))
    print(metrics_df.to_string(index=False))

if __name__=="__main__":
    main()
