#!/usr/bin/env python3
"""Compare every deterministic route artifact for repetition zero.

Run semantic/container auditors separately: this comparison does not validate CRC,
protocol legality, runtime provenance, or search completeness.
"""
import argparse,csv,hashlib,json,struct
from pathlib import Path


def csv_rows(path):
 with path.open() as f:
  reader=csv.DictReader(f)
  yield tuple(reader.fieldnames)
  for row in reader:
   if 'repeat' not in row or row['repeat']=='0':
    yield tuple(row[k] for k in reader.fieldnames)


def equal_bytes(a,b,length=None,offset=0):
 h=hashlib.sha256()
 with a.open('rb') as fa,b.open('rb') as fb:
  fa.seek(offset);fb.seek(offset);left=length
  while left is None or left:
   size=8*1024*1024 if left is None else min(left,8*1024*1024)
   x=fa.read(size);y=fb.read(size)
   assert x==y,(a.name,'payload differs')
   if not x:
    assert left is None,(a.name,'truncated')
    break
   h.update(x)
   if left is not None:left-=len(x)
 return h.hexdigest()


def repeat_extent(path,width=None,variable=False):
 with path.open('rb') as f:
  header=f.read(64);assert len(header)==64
  pos=64
  while True:
   f.seek(pos);prefix=f.read(128 if variable else 8)
   if not prefix:break
   if variable:
    assert len(prefix)==128
    words=struct.unpack('<16Q',prefix);rep=words[1];size=words[7]*8
    assert size>=448
   else:
    assert len(prefix)==8
    rep=struct.unpack('<Q',prefix)[0];size=width
   if rep!=0:break
   pos+=size
  assert pos<=path.stat().st_size
 return pos-64


def compare(case,baseline):
 a=Path(case)/'route';b=Path(baseline)/'route'
 ignored={'audit.json','execution.csv'}
 assert {p.name for p in a.iterdir()}=={p.name for p in b.iterdir()}
 results={}
 widths={'summary_hbm_frames.bin':384,'net_commit_publications.bin':128,'worker_shadow_messages.bin':128}
 for p in sorted(a.iterdir()):
  q=b/p.name
  if p.name in ignored:continue
  if p.suffix=='.csv':
   import itertools
   sentinel=object();h=hashlib.sha256();count=0
   for x,y in itertools.zip_longest(csv_rows(p),csv_rows(q),fillvalue=sentinel):
    assert x==y,(p.name,'repeat-zero rows differ');h.update(json.dumps(x).encode());count+=1
   results[p.name]={'rows_with_header':count,'sha256':h.hexdigest()}
  elif p.name in widths or p.name=='net_commit_frames.bin':
   n=repeat_extent(p,widths.get(p.name),p.name=='net_commit_frames.bin')
   assert n==repeat_extent(q,widths.get(p.name),p.name=='net_commit_frames.bin')
   results[p.name]={'bytes':n,'sha256':equal_bytes(p,q,n,64)}
  elif p.name=='readsets.bin':
   def reads(root):
    with (root/'transactions.csv').open() as f:return sum(int(r['reads']) for r in csv.DictReader(f) if r['repeat']=='0')
   n=reads(a)*16;assert n==reads(b)*16
   results[p.name]={'bytes':n,'sha256':equal_bytes(p,q,n,64)}
  else:results[p.name]={'sha256':equal_bytes(p,q)}
 return {'status':'passed','scope':'deterministic repetition-zero artifacts; separate semantic and XRT audits required','artifacts':results}

if __name__=='__main__':
 if not __debug__:raise RuntimeError('assertions required')
 parser=argparse.ArgumentParser();parser.add_argument('--case',required=True);parser.add_argument('--baseline',required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 result=compare(args.case,args.baseline);args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'artifacts':len(result['artifacts'])}))
