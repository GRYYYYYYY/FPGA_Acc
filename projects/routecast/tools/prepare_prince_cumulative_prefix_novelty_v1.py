"""Freeze complete pre-ready native accepted/pop history, no final labels."""
import json,mmap,struct,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';D=E/'prince_cumulative_prefix_novelty_v1_2026-10-20'
def bounds(mask):return dict(first=(mask&-mask).bit_length() if mask else None,last=mask.bit_length() if mask else None)
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();proofp=S/'branch_inference_verification_v1.json';proof=json.loads(proofp.read_text());design=E/'prince_competitive_support_v1_2026-10-20/cumulative_prefix_novelty_design_v1.json';bindings={str(p):sha(p) for p in [proofp,design,Path(__file__)]};(D/'protocol.json').write_text(json.dumps(dict(design=json.loads(design.read_text()),bindings=dict(bindings),mask='Bit i-1 means observed in native phase i;event counts include multiplicity,entity pairs unique. First/last null if never observed in that tag.',scope='Search-candidate observation is not proof of previous committed routing or future ownership.'),indent=2)+'\n');rows=[]
 for row in proof['rows']:
  case=row['case'].rsplit('/',1)[0]
  if not row['ready']:rows.append(dict(case=case,status='NO_READY_EVENT'));continue
  src=S/row['case'];rp=src/'receipt.json';assert sha(rp)==row['receipt_sha256'];receipt=json.loads(rp.read_text());fp=src/'frontier.bin';assert sha(fp)==receipt['files'][str(fp)];cut=row['cutoff'];counts={};events=0
  with fp.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   assert data[:8]==b'RCFRNT01' and (len(data)-8)%144==0
   for off in range(8,len(data),144):
    tag,phase,net=struct.unpack_from('<QQQ',data,off);assert 1<=phase<=cut
    if tag not in [1,3]:continue
    node=struct.unpack_from('<Q',data,off+56)[0];a=counts.setdefault((net,node),[0,0,0,0]);idx=0 if tag==1 else 2;a[idx]+=1;a[idx+1]|=1<<(phase-1);events+=1
  folder=D/case;folder.mkdir(parents=True);op=folder/'prefix_history.jsonl'
  with op.open('x') as f:
   for (net,node),a in sorted(counts.items()):f.write(json.dumps(dict(net=net,node=node,preheap_events=a[0],preheap_phase_mask=a[1],preheap_first=bounds(a[1])['first'],preheap_last=bounds(a[1])['last'],pop_events=a[2],pop_phase_mask=a[3],pop_first=bounds(a[3])['first'],pop_last=bounds(a[3])['last']),separators=(',',':'))+'\n')
  for p in [rp,fp,op]:bindings[str(p)]=sha(p)
  rows.append(dict(case=case,status='CUMULATIVE_INPUTS_FROZEN_NO_LABELS',ready_iteration=cut,path=str(op),pairs=len(counts),events=events));print('CUMULATIVE_INPUTS_FROZEN',case,len(counts),events,flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());(D/'frozen_inputs.json').write_text(json.dumps(dict(status='CUMULATIVE_NATIVE_PREFIX_FROZEN',rows=rows,bindings=bindings,seconds=time.perf_counter()-start,final_labels_read=False),indent=2)+'\n')
if __name__=='__main__':main()
