"""Reconstruct scoreboards and classify every collision result from HDL logs."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/parmys_collision_xsim_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 result=json.loads((D/'results.json').read_text());assert len(result['rows'])==2;rows=[]
 for row in result['rows']:
  n=row['case'];w=32 if n=='dp13x32' else 36;size=8 if w==32 else 64;mask=(1<<w)-1;score=[i*37+5 for i in range(size)];assert len(row['stages'])==3 and all(s['exit_code']==0 for s in row['stages']);log=(D/n/'xsim.log').read_text();assert 'COLLISION_DIAGNOSTIC_COMPLETE cycles=256' in log;lines=[s.split(',') for s in log.splitlines() if s.startswith('COLLISION,')];assert len(lines)==256
  counts={'reference_mapped_mismatch':0,'source_order_difference':0,'reference_old':0,'reference_new':0,'mapped_old':0,'mapped_new':0,'mapped_mixed_or_other':0,'diagnostic_old':0,'diagnostic_new':0}
  for j,line in enumerate(lines):
   _,idx,addr,*vals=line;assert int(idx)==j and int(addr)==j%size;old,new,ref,mapped,diag=map(lambda x:int(x,16),vals);assert old==score[j%size] and new==((~old)&mask);score[j%size]=new
   counts['reference_mapped_mismatch']+=ref!=mapped;counts['source_order_difference']+=ref!=diag
   for label,value in [('reference',ref),('mapped',mapped),('diagnostic',diag)]:
    if value==old:counts[label+'_old']+=1
    elif value==new:counts[label+'_new']+=1
    elif label=='mapped':counts['mapped_mixed_or_other']+=1
    else:raise AssertionError('non old/new whole-word reference')
  rows.append({'case':n,'collisions':256,'address_count':size,'counts':counts,'bindings':{str(p.relative_to(R)):sha(p) for p in [D/n/'tb.v',D/n/'xsim.log',D/n/'xvlog.stdout.log',D/n/'xelab.stdout.log',D/n/'xsim.stdout.log']}})
 out={'status':'COLLISION_DIAGNOSTIC_HDL_RECEIPTS_VERIFIED','rows':rows,'scope':'Observed behavior for fixed defined collision traces in XSim2022.2. Diagnostic swaps source always-block order only and is not admitted replacement RTL. No source reachability, universal collision equivalence, formal four-state semantics or physical RAM claim.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print(json.dumps([{k:v for k,v in row.items() if k!='bindings'} for row in rows]))
if __name__=='__main__':main()
