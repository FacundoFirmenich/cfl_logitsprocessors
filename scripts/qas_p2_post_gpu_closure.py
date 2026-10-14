#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, hashlib, json, math, shutil, tempfile, zipfile
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from jsonschema import Draft202012Validator

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b: return 1.0
    return len(a & b) / len(a | b)

def quantile(xs, q):
    xs=sorted(xs)
    if not xs: return None
    if len(xs)==1: return xs[0]
    pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi: return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w

def unpack(input_path: Path):
    if input_path.is_dir():
        return input_path, None
    tmp=Path(tempfile.mkdtemp(prefix='qas_p2_closure_'))
    with zipfile.ZipFile(input_path) as z:
        bad=z.testzip()
        if bad: raise SystemExit(f'corrupt ZIP member: {bad}')
        z.extractall(tmp)
    candidates=[tmp]+[p for p in tmp.iterdir() if p.is_dir()]
    for c in candidates:
        if (c/'qas_p2_evidence_receipts.jsonl').exists(): return c,tmp
    raise SystemExit('QAS-P2 receipt file not found in ZIP')

def validate(root: Path, schema_path: Path):
    schema=json.loads(schema_path.read_text())
    validator=Draft202012Validator(schema)
    receipts=[]
    for n,line in enumerate((root/'qas_p2_evidence_receipts.jsonl').read_text().splitlines(),1):
        if not line.strip(): continue
        r=json.loads(line)
        errors=list(validator.iter_errors(r))
        if errors: raise SystemExit(f'receipt line {n}: {errors[0].message}')
        exact_hash=sha256_bytes(json.dumps(sorted(r['support_ids']),separators=(',',':')).encode())
        if exact_hash != r['support_hash']:
            raise SystemExit(f'receipt line {n}: support hash mismatch')
        if len(r['baseline_top64_ids']) != len(r['baseline_top64_probs']):
            raise SystemExit(f'receipt line {n}: candidate lengths mismatch')
        receipts.append(r)
    if not receipts: raise SystemExit('no QAS-P2 receipts')
    return receipts

def summarize(receipts):
    rows=[]; violations=[]
    for r in receipts:
        s=set(r['support_ids']); c=set(r['baseline_top64_ids'])
        inter=len(s & c); recall=inter/max(1,len(s)); outside=sorted(s-c)
        row={
            'run_id':r['run_id'],'prompt_hash':r['prompt_hash'],'seed':r['seed'],
            'step_index':r['step_index'],'operator_id':r['operator_id'],
            'support_hash':r['support_hash'],'support_size':r['support_size'],
            'support_fraction':r['support_fraction'],'candidate_count':len(c),
            'candidate_support_intersection':inter,'candidate_support_recall':recall,
            'outside_top64_count':len(outside),'activity_metric':r.get('activity_metric'),
            'target_reached':r.get('fidelity_endpoint',{}).get('target_reached'),
        }
        rows.append(row)
        if outside: violations.append({**row,'outside_top64_ids':outside})

    by_run=defaultdict(list)
    for r in receipts: by_run[r['run_id']].append(r)
    mobility=[]
    for run_id,rs in by_run.items():
        rs=sorted(rs,key=lambda x:x['step_index'])
        for a,b in zip(rs,rs[1:]):
            mobility.append({
                'run_id':run_id,'operator_id':b['operator_id'],
                'step_from':a['step_index'],'step_to':b['step_index'],
                'support_jaccard':jaccard(a['support_ids'],b['support_ids'])
            })

    sizes=[x['support_size'] for x in rows]
    recalls=[x['candidate_support_recall'] for x in rows]
    acts=[x['activity_metric'] for x in rows if isinstance(x['activity_metric'],(int,float)) and math.isfinite(x['activity_metric'])]
    js=[x['support_jaccard'] for x in mobility]
    operator=[]
    for op in sorted({x['operator_id'] for x in rows}):
        sub=[x for x in rows if x['operator_id']==op]
        operator.append({
            'operator_id':op,'n_steps':len(sub),
            'support_size_mean':mean([x['support_size'] for x in sub]),
            'support_size_median':median([x['support_size'] for x in sub]),
            'candidate_recall_mean':mean([x['candidate_support_recall'] for x in sub]),
            'candidate_recall_min':min(x['candidate_support_recall'] for x in sub),
            'top64_violation_steps':sum(x['outside_top64_count']>0 for x in sub),
            'active_steps':sum((x['activity_metric'] or 0)>0 for x in sub if x['activity_metric'] is not None),
        })

    global_summary={
        'receipt_count':len(receipts),'run_count':len(by_run),
        'operator_count':len({r['operator_id'] for r in receipts}),
        'unique_support_hashes':len({r['support_hash'] for r in receipts}),
        'support_size_mean':mean(sizes),'support_size_median':median(sizes),
        'support_size_q05':quantile(sizes,.05),'support_size_q95':quantile(sizes,.95),
        'candidate_recall_mean':mean(recalls),'candidate_recall_median':median(recalls),
        'candidate_recall_min':min(recalls),'top64_violation_steps':len(violations),
        'top64_status':'FALSIFIED' if violations else 'PASSED_FROZEN_CAMPAIGN',
        'activity_metric_mean':mean(acts) if acts else None,
        'successive_support_jaccard_mean':mean(js) if js else None,
        'successive_support_jaccard_median':median(js) if js else None,
    }
    return rows,mobility,operator,violations,global_summary

def write_csv(path, rows):
    if not rows:
        path.write_text(''); return
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('input',type=Path)
    p.add_argument('--schema',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    root,tmp=unpack(args.input); out=args.output; out.mkdir(parents=True,exist_ok=True)
    receipts=validate(root,args.schema)
    rows,mobility,operator,violations,summary=summarize(receipts)
    write_csv(out/'step_geometry.csv',rows)
    write_csv(out/'support_mobility.csv',mobility)
    write_csv(out/'operator_local_summary.csv',operator)
    (out/'top64_violations.json').write_text(json.dumps(violations,indent=2))
    (out/'global_summary.json').write_text(json.dumps(summary,indent=2))

    decision={
        'schema':'qas.p2.post_gpu_decision.v1',
        'frozen_test':'TOP64_UNIVERSAL_CANDIDATE_SUFFICIENCY',
        'top64_status':summary['top64_status'],
        'next_architecture_branch':(
            'GENERATOR_BRANCH_REQUIRED_FOR_EXACT_MASK_IMITATION'
            if violations else
            'RERANKER_BRANCH_ELIGIBLE_FOR_SEPARATE_PREREGISTRATION'
        ),
        'interpretation_boundary':(
            'This selects the next experimental architecture only. It does not prove '
            'support necessity/minimality, deployment speedup, or authority.'
        ),
        'permission_granted':False,
    }
    (out/'NEXT_ARCHITECTURE_DECISION.json').write_text(json.dumps(decision,indent=2))
    bundle={
        'schema':'qas.p2.ech_cas_rdss_bundle.v1',
        'source_receipt_sha256':sha256_file(root/'qas_p2_evidence_receipts.jsonl'),
        'model_revisions':sorted({r['model_revision'] for r in receipts}),
        'tokenizer_hashes':sorted({r['tokenizer_hash'] for r in receipts}),
        'prompt_hashes':sorted({r['prompt_hash'] for r in receipts}),
        'operators':sorted({r['operator_id'] for r in receipts}),
        'global_summary':summary,
        'jurisdiction_status':'DESCRIPTIVE_ONLY_NO_RDSS_AUTHORITY_FIT_YET',
        'cas_status':'OBSERVED_HEURISTIC_SUPPORTS_NOT_MINIMALITY_CERTIFICATES',
        'kch_status':'EVIDENCE_BUNDLE_ONLY_REQUIRES_SEPARATE_LEASE',
        'permission_granted':False,
    }
    (out/'ECH_CAS_RDSS_KCH_BUNDLE.json').write_text(json.dumps(bundle,indent=2))
    hashes=[]
    for f in sorted(out.iterdir()):
        if f.is_file() and f.name!='SHA256SUMS.txt': hashes.append(f'{sha256_file(f)}  {f.name}')
    (out/'SHA256SUMS.txt').write_text('\n'.join(hashes)+'\n')
    print(json.dumps({'status':'PASS',**summary,'decision':decision['next_architecture_branch']},indent=2))
    if tmp: shutil.rmtree(tmp)

if __name__=='__main__': main()
