"""Recover the immutable QAS v3.8.2 notebook; never alter scientific inputs."""
from __future__ import annotations
import argparse, base64, hashlib, json, lzma, os, re, urllib.request
from pathlib import Path

TREE = 'cf8f84e577525a2addd83b259d81a60172d64fe6'
OLD_SHA = '65c4bb2244e8462f9f76edfe4307c4b2b3fb7525928cdd9f327e3aab479dd082'
SEG_SHA = 'd303c19b9ba10b1dbea7bbba53a4e91e9bf43a5437c8b45eccd7992c48066add'
NEW_SHA = 'ffd12bc723fcdaf67782bbf8c3e2cfc5a1af6ac143dd0c79fdd3723089442c9a'
NOTEBOOK_SHA = 'cc1675e1bca388c055b949954e4a993f4ea415e9f02cd9d317cf2531f17a41b4'
REPLACEMENT = bytes.fromhex('f95a6d8b5d8502f7c77be00216a4d01946d4d23ccbc32f577ceff0c2f9a37a9fa5b1c2d737de078e22f4df28eb7a523ff6aacc324e921215b00eab6b33fc50016e2ba03769ded41b15835bdab60a390bd4cf2d2a27')

def sha(x): return hashlib.sha256(x).hexdigest()

def repair(packed: bytes) -> bytes:
    if sha(packed) != OLD_SHA: raise ValueError('Unexpected compressed source: no repair applied')
    if sha(packed[54873:54958]) != SEG_SHA: raise ValueError('Unexpected damaged segment')
    fixed = packed[:54873] + REPLACEMENT + packed[54958:]
    if sha(fixed) != NEW_SHA: raise ValueError('Repaired stream hash mismatch')
    raw = lzma.decompress(fixed)
    if len(raw) != 221723 or sha(raw) != NOTEBOOK_SHA: raise ValueError('Frozen notebook mismatch')
    return raw

def retrieve():
    api = 'https://api.github.com/repos/FacundoFirmenich/cfl_logitsprocessors'
    def get(path):
        headers = {'Accept': 'application/vnd.github+json'}
        if os.environ.get('GH_READ_TOKEN'): headers['Authorization'] = 'Bearer ' + os.environ['GH_READ_TOKEN']
        with urllib.request.urlopen(urllib.request.Request(api + path, headers=headers), timeout=30) as response:
            return json.load(response)
    tree = get('/git/trees/' + TREE)
    if tree.get('truncated'): raise ValueError('Truncated tree')
    encoded = []
    for entry in sorted(tree['tree'], key=lambda e:e['path']):
        if not re.fullmatch(r'notebook\.b64\.part\d{2}(\.suf\d{2})?', entry['path']): raise ValueError('Unexpected chunk')
        blob = get('/git/blobs/' + entry['sha'])
        raw = base64.b64decode(blob['content'])
        if hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() != entry['sha']:
            raise ValueError('Git blob hash mismatch')
        encoded.append(b''.join(raw.split()))
    return base64.b64decode(b''.join(encoded), validate=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--packed', type=Path)
    parser.add_argument('--out', type=Path, default=Path('run'))
    args=parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    receipt={'gpu_campaign_launched':False, 'expected_notebook_sha256':NOTEBOOK_SHA}
    try:
        packed=args.packed.read_bytes() if args.packed else retrieve()
        raw=repair(packed); notebook=json.loads(raw); cells=[]
        for i, cell in enumerate(notebook['cells']):
            if cell.get('cell_type') != 'code': continue
            source=''.join(cell.get('source',[])); compile(source, 'cell_'+str(i), 'exec'); cells.append(source)
        script='\n\n'.join(cells)
        old='os.kill(os.getpid(), signal.SIGKILL)'
        if script.count(old) != 1: raise ValueError('Unexpected bootstrap restart count')
        script=script.replace(old,'os.execv(sys.executable, [sys.executable, __file__])',1)
        compile(script,'run_qas_v382.py','exec')
        (args.out/'frozen_notebook.ipynb').write_bytes(raw)
        (args.out/'run_qas_v382.py').write_text(script,encoding='utf-8')
        receipt.update(status='EXACT_FROZEN_NOTEBOOK_RECOVERED', notebook_bytes=len(raw), notebook_sha256=sha(raw), code_cells=len(cells), launcher_sha256=sha(script.encode()), repaired_compressed_bytes=85, transport_only_restart_change=True)
    except Exception as exc:
        receipt.update(status='RECOVERY_BLOCKED',error=type(exc).__name__+': '+str(exc)); raise
    finally:
        (args.out/'recovery_receipt.json').write_text(json.dumps(receipt,indent=2))
        print(json.dumps(receipt,indent=2))

if __name__=='__main__': main()
