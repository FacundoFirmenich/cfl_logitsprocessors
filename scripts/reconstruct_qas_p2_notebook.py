#!/usr/bin/env python3
from __future__ import annotations
import argparse, base64, hashlib, lzma
from pathlib import Path

EXPECTED_SHA256 = "bb72c30b5d19b8c6b09cb7332e9962d4aa6927aaae01afebafaca5c90eb552b9"

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--repo-root', type=Path, default=Path('.'))
    a=p.parse_args()
    root=a.repo_root.resolve()
    chunk_dir=root/'experiments/qas_p2_label_complete_2026_10_14/notebook_chunks'
    chunks=[chunk_dir/f'notebook.b64.part{i:02d}' for i in range(9)]
    missing=[str(x) for x in chunks if not x.exists()]
    if missing:
        raise SystemExit('missing notebook chunks: '+', '.join(missing))
    b64=''.join(''.join(x.read_text().split()) for x in chunks)
    raw=lzma.decompress(base64.b64decode(b64))
    digest=hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SHA256:
        raise SystemExit(f'notebook SHA256 mismatch: {digest}')
    out=root/'notebooks/RDS_V3_8_QAS_P2_LABEL_COMPLETE_QWEN35_4B_COLAB_GPU.ipynb'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_bytes(raw)
    print(out)
    print(digest)

if __name__=='__main__':
    main()
