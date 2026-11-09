#!/usr/bin/env python3
"""Replay recorded first-repeat occupancy and identify strict SLL conflicts.

Counterfactual diagnostics only: denied proposals need new searches/scheduling,
so these records do not prove strict-mode convergence or runtime behavior.
"""
import argparse,csv,hashlib,json,mmap
from collections import defaultdict
from pathlib import Path
import struct


def analyze(run):
 run=Path(run);manifest=json.loads((run/'manifest.json').read_text());assert manifest['status']=='passed'
 route=run/'route'
 def rows(name):
  with (route/name).open() as f:return [r for r in csv.DictReader(f) if 'repeat' not in r or r['repeat']=='0']
 selection=rows('selection.csv');roots={int(r['net']):int(r['source']) for r in selection}
 trees={net:{root} for net,root in roots.items()};owners=defaultdict(set)
 for net,root in roots.items():owners[root].add(net)
 paths=defaultdict(set)
 for r in rows('proposal_paths.csv'):
  key=tuple(int(r[k]) for k in ['iteration','wave','slot','attempt']);paths[key].add(int(r['destination']))
 transactions=rows('transactions.csv');by_epoch=defaultdict(list)
 for r in transactions:by_epoch[int(r['iteration'])].append(r)
 epochs=[];conflicts=[]
 with (Path(manifest['command'][1])/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nodes:
  def boundary(n):
   assert n<len(nodes)//64
   mask=struct.unpack_from('<I',nodes,n*64+20)[0];return bool(mask&(mask-1))
  for epoch,txs in sorted(by_epoch.items()):
   if epoch:
    for net in {int(r['net']) for r in txs}:
     for n in trees[net]-{roots[net]}:owners[n].remove(net)
     trees[net]={roots[net]}
   for r in txs:
    if r['committed']!='1':continue
    net=int(r['net']);key=tuple(int(r[k]) for k in ['iteration','wave','slot','attempt']);writes=paths[key]
    sll=[n for n in sorted(writes) if boundary(n)]
    denied=[{'node':n,'other_nets':sorted(owners[n]-{net})} for n in sll if owners[n]-{net}]
    if denied:conflicts.append({'iteration':epoch,'wave':key[1],'slot':key[2],'attempt':key[3],'net':net,'SLL_conflicts':denied})
    for n in writes:owners[n].add(net)
    trees[net].update(writes)
   epochs.append({'iteration':epoch,'overused_nodes':sum(len(v)>1 for v in owners.values()),'overused_SLL_nodes':sum(len(v)>1 and boundary(n) for n,v in owners.items())})
  expected=defaultdict(set)
  for r in rows('usage.csv'):
   if int(r['net'])!=UINT32_MAX:expected[int(r['node'])].add(int(r['net']))
  assert {n:v for n,v in owners.items() if v}==dict(expected),'final occupancy replay differs'
  reported=rows('iterations.csv')
  assert [(e['iteration'],e['overused_nodes']) for e in epochs]==[(int(r['iteration']),int(r['overused_nodes'])) for r in reported]
 inputs={name:hashlib.sha256((route/name).read_bytes()).hexdigest() for name in ['selection.csv','proposal_paths.csv','transactions.csv','usage.csv','iterations.csv']}
 for name,digest in inputs.items():assert manifest['artifacts']['route/'+name]==digest,name
 return {'status':'passed','scope':'Recorded negotiated-route first-repeat occupancy replay; strict grant counterfactual only, no strict rerouting/convergence or hardware claim','epochs':epochs,'strict_SLL_denied_recorded_commits':len(conflicts),'conflicts':conflicts,'final_occupancy_verified':True,'artifact_sha256':inputs,'graph_nodes_reference_sha256':manifest['inputs'].get(str(Path(manifest['command'][1])/'nodes.bin')),'board_result':False}

UINT32_MAX=(1<<32)-1
if __name__=='__main__':
 if not __debug__:raise RuntimeError('assertions required')
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=analyze(a.run);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['artifact_sha256','conflicts']}))
