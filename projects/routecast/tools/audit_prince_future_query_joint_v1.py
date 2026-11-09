"""Independent future-query scan and typed conditional-moment verification."""
import json,struct
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_future_query_joint_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def main():
 x=load(D/'dataset_manifest.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 bycase=defaultdict(list)
 for r in x['rows']:
  if r['status']=='FUTURE_QUERY_LABELS_EXTRACTED':bycase[r['case']].append(r)
 total=groups=unqueried=resources=0
 for case,rows in bycase.items():
  raw=E/'prince_connection_query_trial_v1_2026-10-20'/case/'capture/queries.tsv';phases={r['query_iteration']:r['horizon'] for r in rows};expected=Counter();counts=Counter()
  for line in raw.open():
   fields=line.split('\t');phase=int(fields[0])
   if phase not in phases or fields[3] not in ['4','5']:continue
   node=int(fields[2]);o=int(fields[4])-int(fields[15]);own=int(fields[15]);acc=int(fields[7]);n=int(fields[16]);h=phases[phase];expected[h,node,acc,o,own]+=n;counts[h,node]+=1
  for row in rows:
   h=row['horizon'];records=list(map(json.loads,Path(row['target_file']).open()));assert len(records)==row['resources'];assert len({r['id'] for r in records})==len(records);cs=gs=qs=0
   for r in records:
    c=Counter({(h,r['id'],a['acc_bits'],a['F_other'],a['I_retained']):a['calls'] for a in r['joint']});assert len(c)==len(r['joint']);assert all(expected.pop(k)==v for k,v in c.items());assert counts[h,r['id']]==r['state_groups'];assert sum(c.values())==r['calls'];n=r['calls'];cs+=n;gs+=r['state_groups'];qs+=bool(n);resources+=1
    if not n:assert r['moment_sums'] is None and not r['joint'];unqueried+=1;continue
    arrays=[]
    for a in r['joint']:
     val=struct.unpack('<f',a['acc_bits'].to_bytes(4,'little'))[0];assert int(val)==val;arrays.append((int(val),a['F_other'],a['I_retained'],a['calls']))
    sums=[sum(a*v for a,o,i,v in arrays),sum(o*v for a,o,i,v in arrays),sum(a*o*v for a,o,i,v in arrays),sum(i*v for a,o,i,v in arrays),sum(a*i*v for a,o,i,v in arrays)];assert sums==[r['moment_sums'][k] for k in ['A','F_other','A_F_other','I_retained','A_I_retained']];assert n*sums[2]==sums[0]*sums[1]
   assert (cs,gs,qs)==(row['cost_calls'],row['state_groups'],row['queried_resources']);total+=cs;groups+=gs
  assert not expected
 assert total==x['cost_calls'] and groups==x['state_groups'] and len(x['rows'])==18 and len(bycase)==6
 out=dict(status='ALL12_FUTURE_QUERY_FRAMES_INDEPENDENTLY_RESCANNED',resource_rows=resources,no_query_resource_rows=unqueried,cost_calls=total,state_groups=groups,scope='Independent raw-field scan,call histograms and integer moments;future A coherence previously checked against native phase words. No-query moments remain null. No predictor/native admission.',bindings={str(p):sha(p) for p in [D/'dataset_manifest.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'],total,resources,unqueried)
if __name__=='__main__':main()
