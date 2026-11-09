"""Freeze causal competitive support counts before final label join."""
import json,mmap,struct,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';D=E/'prince_competitive_support_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();proofp=S/'branch_inference_verification_v1.json';proof=json.loads(proofp.read_text());design=S/'competitive_support_screen_design_v1.json';bindings={str(p):sha(p) for p in [proofp,design,Path(__file__)]};rows=[]
 (D/'protocol.json').write_text(json.dumps(dict(design=json.loads(design.read_text()),producer='Only tag1/tag3 at phases ready-1,ready;record counts per NET/node. No final-label file read;original query support remains independent comparator.',bindings=dict(bindings)),indent=2)+'\n')
 for row in proof['rows']:
  case=row['case'].rsplit('/',1)[0]
  if not row['ready']:rows.append(dict(case=case,status='NO_READY_EVENT'));continue
  d=S/row['case'];rp=d/'receipt.json';assert sha(rp)==row['receipt_sha256'];receipt=json.loads(rp.read_text());fp=d/'frontier.bin';assert sha(fp)==receipt['files'][str(fp)];t=row['cutoff'];counts={t-1:Counter(),t:Counter()};eventcounts=Counter()
  with fp.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   assert data[:8]==b'RCFRNT01' and (len(data)-8)%144==0
   for off in range(8,len(data),144):
    tag,i=struct.unpack_from('<QQ',data,off)
    if i not in counts or tag not in [1,3]:continue
    net=struct.unpack_from('<Q',data,off+16)[0];node=struct.unpack_from('<Q',data,off+56)[0];counts[i][net,node,tag]+=1;eventcounts[i,tag]+=1
  out=D/case;out.mkdir(parents=True);paths={}
  for i,cnt in counts.items():
   pairs=sorted({(net,node) for net,node,tag in cnt});p=out/f'support_iteration_{i}.jsonl'
   with p.open('x') as f:
    for net,node in pairs:f.write(json.dumps(dict(iteration=i,net=net,node=node,preheap_accepted=cnt[net,node,1],valid_pop=cnt[net,node,3]),separators=(',',':'))+'\n')
   paths[str(i)]=str(p);bindings[str(p)]=sha(p)
  for p in [rp,fp]:bindings[str(p)]=sha(p)
  rows.append(dict(case=case,status='COMPETITIVE_SUPPORT_FROZEN_NO_LABELS',ready_iteration=t,paths=paths,event_counts={f'{i},{tag}':n for (i,tag),n in sorted(eventcounts.items())}));print('COMPETITIVE_SUPPORT_FROZEN',case,dict(eventcounts),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 (D/'frozen_inputs.json').write_text(json.dumps(dict(status='CAUSAL_COMPETITIVE_SUPPORT_FROZEN',rows=rows,bindings=bindings,seconds=time.perf_counter()-start,final_labels_read=False),indent=2)+'\n')
if __name__=='__main__':main()
