from __future__ import annotations
import hashlib,json,re,shutil,unicodedata,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
WORKSPACE=HERE.parents[1]
DEV=WORKSPACE/'paper_aaai27'/'rds_architecture_v0_3_0_dev'
DOC=HERE/'RDS_EXPANDED_ARCHITECTURE_PREREGISTRATION_v1.0.md'
SNAPSHOT=HERE/'frozen_snapshot'
SOURCES=[DEV/'architecture'/'EXACT_ACTION_REGISTRY_v1.0.json',DEV/'configs'/'models_v1.json',DEV/'configs'/'laboratory_phases_v1.json',*sorted((DEV/'prompts').glob('*.json'))]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
 return h.hexdigest()
def main():
 text=unicodedata.normalize('NFC',DOC.read_text(encoding='utf-8-sig')).replace('\r\n','\n').replace('\r','\n')
 DOC.write_text(text,encoding='utf-8',newline='\n')
 if SNAPSHOT.exists(): shutil.rmtree(SNAPSHOT)
 for src in SOURCES:
  dst=SNAPSHOT/src.relative_to(DEV); dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
 pattern=re.compile(r'^- \*\*(H\d{2}) ([^*]+):\*\* (.+)$')
 rows=[]
 for line in text.splitlines():
  m=pattern.match(line)
  if m: rows.append({'prediction_id':m.group(1),'label':m.group(2),'statement':m.group(3)})
 expected=[f'H{i:02d}' for i in range(1,38)]
 if [r['prediction_id'] for r in rows]!=expected: raise RuntimeError('prediction sequence mismatch')
 pred=HERE/'PREDICTIONS.json'; pred.write_text(json.dumps({'schema':'rds-preregistered-predictions-v1','count':len(rows),'predictions':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 payload=[DOC,pred,HERE/'CLAIM_TRACEABILITY.md',*sorted(p for p in SNAPSHOT.rglob('*') if p.is_file())]
 entries=sorted(({'path':p.relative_to(HERE).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in payload),key=lambda r:r['path'])
 ledger=json.dumps(entries,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 prehash=hashlib.sha256(ledger).hexdigest()
 manifest={'schema':'rds-preregistration-manifest-v1','status':'prospective_pre_experimental','freeze_date':'2026-07-02','hash_algorithm':'SHA-256','root_prehash_definition':'sha256(canonical-json(sorted payload entries[path,bytes,sha256]))','root_prehash':prehash,'payload_count':len(entries),'payload':entries,'post_upload_fields':{'git_commit':None,'signed_tag':None,'github_release':None,'zenodo_version_doi':None,'zenodo_concept_doi':None}}
 (HERE/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
 (HERE/'SHA256SUMS.txt').write_text(''.join(f"{e['sha256']}  {e['path']}\n" for e in entries),encoding='utf-8',newline='\n')
 (HERE/'PREHASH.sha256').write_text(f'{prehash}  RDS_EXPANDED_ARCHITECTURE_PREREGISTRATION_v1.0.payload-ledger\n',encoding='ascii',newline='\n')
 archive=HERE/'RDS_EXPANDED_ARCHITECTURE_PREREGISTRATION_v1.0_ZENODO.zip'
 members=payload+[HERE/'MANIFEST.json',HERE/'SHA256SUMS.txt',HERE/'PREHASH.sha256']
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for item in sorted(members,key=lambda q:q.relative_to(HERE).as_posix()):
   name=item.relative_to(HERE).as_posix(); info=zipfile.ZipInfo(name,date_time=(2026,7,2,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16; z.writestr(info,item.read_bytes())
 print(json.dumps({'root_prehash':prehash,'archive_sha256':sha(archive),'payload_count':len(entries),'predictions':len(rows)},indent=2))
if __name__=='__main__': main()