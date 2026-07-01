from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 m=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
 errors=[]
 for row in m['payload']:
  p=ROOT/row['path']
  if not p.is_file(): errors.append(f"missing:{row['path']}"); continue
  if p.stat().st_size!=row['bytes']: errors.append(f"bytes:{row['path']}")
  if sha(p)!=row['sha256']: errors.append(f"sha256:{row['path']}")
 ledger=json.dumps(m['payload'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
 root=hashlib.sha256(ledger).hexdigest()
 if root!=m['root_prehash']: errors.append('root_prehash')
 sums={line.split('  ',1)[1]:line.split('  ',1)[0] for line in (ROOT/'SHA256SUMS.txt').read_text().splitlines()}
 if sums!={r['path']:r['sha256'] for r in m['payload']}: errors.append('sha256sums')
 print(json.dumps({'valid':not errors,'root_prehash':root,'payload_count':len(m['payload']),'errors':errors},indent=2))
 return 1 if errors else 0
if __name__=='__main__': sys.exit(main())