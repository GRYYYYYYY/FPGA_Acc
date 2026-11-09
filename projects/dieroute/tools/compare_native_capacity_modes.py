#!/usr/bin/env python3
"""Compare fully audited native model work; never infer physical speed/QoR."""
import argparse,csv,hashlib,json,mmap,struct
from pathlib import Path


def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
 return h.hexdigest()


def summarize(run,audit):
 run=Path(run).resolve();audit=Path(audit).resolve();manifest=json.loads((run/'manifest.json').read_text());proof=json.loads((audit/'audit.json').read_text())
 assert manifest['status']=='passed' and manifest['inputs_unchanged'] and proof['passed'] and proof['inputs_unchanged'] and proof['net_commit']['verified']
 assert proof['inputs'][str(run/'manifest.json')]==sha(run/'manifest.json')
 names=['iterations.csv','trees.csv','usage.csv','selection.csv'];bindings={}
 for name in names:
  p=run/'route'/name;digest=sha(p);assert manifest['artifacts']['route/'+name]==digest;bindings[name]=digest
 def rows(name):
  with (run/'route'/name).open() as f:return [r for r in csv.DictReader(f) if 'repeat' not in r or r['repeat']=='0']
 iterations=rows('iterations.csv');trees=rows('trees.csv');usage=rows('usage.csv');selection=rows('selection.csv')
 graph=Path(manifest['command'][1]);boundary=set()
 with (graph/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as nodes:
  for r in usage:
   if int(r['net'])==(1<<32)-1:continue
   n=int(r['node']);mask=struct.unpack_from('<I',nodes,n*64+20)[0]
   if mask&(mask-1):boundary.add(n)
 work={name:sum(int(r[name]) for r in iterations) for name in ['expanded','edge_visits','quotient_expanded','quotient_edge_visits']}
 result={'repeats_audited':proof['repeats'],'first_repeat_epochs':len(iterations),'selected_nets':len({r['net'] for r in selection}),'tasks':len(selection),'first_repeat_work':work,'first_repeat_tree_PIPs':sum(int(r['parent'])!=(1<<32)-1 for r in trees),'first_repeat_occupied_boundary_nodes':len(boundary),'first_repeat_final_overuse':int(iterations[-1]['overused_nodes']),'kernel_calls_all_repeats':proof['net_commit']['kernel_calls'],'artifact_sha256':bindings,'protocol_audit_sha256':sha(audit/'audit.json'),'run_manifest_sha256':sha(run/'manifest.json')}
 return result,manifest


def main():
 if not __debug__:raise RuntimeError('assertions required')
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['baseline','baseline-audit','strict','strict-audit','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();base,bm=summarize(a.baseline,a.baseline_audit);strict,sm=summarize(a.strict,a.strict_audit)
 assert bm['command'][1:7]==sm['command'][1:7] and bm['command'][8:]==sm['command'][8:]
 assert base['artifact_sha256']['selection.csv']==strict['artifact_sha256']['selection.csv']
 result={'status':'passed','scope':'Audited model work and selected electrical-route counts on fixed common inputs; no physical length, timing, speed or energy claim','baseline':base,'strict':strict,'work_deltas_strict_minus_baseline':{name:strict['first_repeat_work'][name]-value for name,value in base['first_repeat_work'].items()},'board_result':False}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k in ['status','work_deltas_strict_minus_baseline']}))

if __name__=='__main__':main()
