#!/usr/bin/env python3
"""Check the pinned carrier snapshot against HF LFS SHA256 and Git blob identities."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory',type=Path)
parser.add_argument('--existing',action='store_true',help='Report partial verification; never mark an incomplete snapshot passed')
args=parser.parse_args()
manifest=json.loads((ROOT/'data/carrier-files.json').read_text())
lock=json.loads((ROOT/'sources.lock.json').read_text())['carrier']
assert all(manifest[k]==lock[k] for k in ('repo_id','revision')), 'Carrier identity differs from lock'
missing=[];verified=0
for record in manifest['files']:
 relative=Path(record['path'])
 if relative.is_absolute() or '..' in relative.parts:raise ValueError('Unsafe carrier path')
 path=args.directory/relative
 if not path.is_file():
  missing.append(str(relative))
  if not args.existing:raise FileNotFoundError(path)
  continue
 size=path.stat().st_size
 if size!=record['bytes']:raise ValueError(f'Size mismatch: {path}')
 if record['algorithm']=='sha256':digest=hashlib.sha256()
 elif record['algorithm']=='git-blob-sha1':
  digest=hashlib.sha1();digest.update(f'blob {size}\0'.encode())
 else:raise ValueError('Unknown digest algorithm')
 with path.open('rb') as source:
  while block:=source.read(8*1024*1024):digest.update(block)
 if digest.hexdigest()!=record['digest']:raise ValueError(f'Hash mismatch: {path}')
 verified+=1
 print(json.dumps({'path':str(relative),'bytes':size,'algorithm':record['algorithm'],
                   'digest':digest.hexdigest(),'status':'verified'}),flush=True)
print(json.dumps({'status':'partial' if missing else 'passed','verified':verified,
                  'missing':missing,'revision':manifest['revision']}),flush=True)
