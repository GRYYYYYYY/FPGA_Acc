#!/usr/bin/env python3
"""Independently replay original-tree resource closure and candidate membership."""
import argparse,csv,json,hashlib
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def trees(p):
 result={}
 for r in csv.DictReader(p.open()):
  assert r['repeat']=='0'
  net=int(r['net']);node=int(r['node']);row=tuple(int(r[k]) for k in ['parent','pip_key','depth'])
  assert node not in result.setdefault(net,{})
  result[net][node]=row
 return result

def main():
 a=argparse.ArgumentParser();a.add_argument('run',type=Path);a.add_argument('output',type=Path);x=a.parse_args();x.run=x.run.resolve();x.output=x.output.resolve();m=json.loads((x.run/'manifest.json').read_text());assert m['status']=='repair_candidates_generated'
 inputs={str(x.run/'manifest.json'):sha(x.run/'manifest.json')};cases={}
 for kind in ['baseline','strict']:
  base=x.run/kind;files=[base/'baseline/trees.csv',base/'proposal/trees.csv',base/'candidate/trees.csv',base/'candidate/usage.csv',base/'decision.json'];inputs.update({str(p):sha(p) for p in files});old,proposal,candidate=[trees(p) for p in files[:3]];assert old.keys()==proposal.keys()==candidate.keys() and len(old)==341
  decision=json.loads(files[4].read_text());assert not decision['native_timing_accepted'];closure={455288,456285};uses={}
  for net,nodes in proposal.items():
   for node in nodes:uses.setdefault(node,set()).add(net)
  while True:
   more=closure|{net for n in closure for node in old[n] for net in uses.get(node,set())}
   if more==closure:break
   closure=more
  assert closure==set(decision['restored_nets'])
  for net in candidate:assert candidate[net]==(old[net] if net in closure else proposal[net])
  expected={}
  for net,nodes in candidate.items():
   for node in nodes:expected.setdefault(node,set()).add(net)
  assert all(len(nets)==1 for nets in expected.values())
  actual={}
  for r in csv.DictReader(files[3].open()):
   assert r['repeat']=='0' and int(r['version'])>0
   if int(r['net'])!=4294967295:assert int(r['net']) not in actual.setdefault(int(r['node']),set());actual[int(r['node'])].add(int(r['net']))
  assert actual==expected
  cases[kind]={'restored_nets':sorted(closure),'nets':len(candidate),'tree_pips':sum(len(t)-1 for t in candidate.values()),'exact_expected_trees':True,'zero_selected_resource_conflicts':True,'exact_usage_membership':True}
 assert all(sha(p)==h for p,h in inputs.items());assert not x.output.exists();x.output.mkdir();(x.output/'audit.json').write_text(json.dumps({'passed':True,'cases':cases,'inputs':inputs,'scope':'Independent restoration closure, exact trees and selected usage membership. Original graph provenance, physical writeback and native timing remain separate.','native_timing_accepted':False,'board_result':False},indent=2)+'\n');print(json.dumps(cases))
if __name__=='__main__':main()
