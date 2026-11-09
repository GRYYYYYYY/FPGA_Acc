"""Freeze actual search scopes and exact same-attempt margin minima, no labels."""
import json,struct,subprocess
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_search_attempt_trial_v1_2026-10-20';D=E/'prince_attempt_scope_competition_v1_2026-10-20';B=R/'build/prince_attempt_competition_v1_2026-10-20/extract'
def load(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);proofp=S/'attempt_inference_verification_v1.json';proof=load(proofp);oldp=E/'prince_competitive_frontier_trial_v1_2026-10-20/branch_inference_verification_v1.json';old={r['case']:r for r in load(oldp)['rows']};design=S/'actual_attempt_scope_and_competition_design_v1.json';bindings={str(p):sha(p) for p in [proofp,oldp,design,Path(__file__),B,R/'tools/extract_prince_attempt_margins_v1.cpp']};(D/'protocol.json').write_text(json.dumps(dict(design=load(design),bindings=dict(bindings),minimum_order='Exact float32 ratio F_candidate/F_sink ordering via signed dyadic mantissa products;subtracting1 preserves min order. Strict tie keeps earliest event. Independent rational audit required.',scope='Source target outcomes from completed pre-ready attempts only. Geometry deduplicates actual boxes per phase/NET,retains attempt multiplicity. No final labels read.'),indent=2)+'\n');rows=[]
 for row in proof['rows']:
  c=row['case'].rsplit('/',1)[0]
  if not row['ready']:rows.append(dict(case=c,status='NO_READY_EVENT'));continue
  src=S/row['case'];rp=src/'receipt.json';assert sha(rp)==row['receipt_sha256'];receipt=load(rp);t=row['cutoff'];mp=src/'frontier.bin.attempts.bin';ep=src/'frontier.bin'
  for p in [mp,ep]:assert sha(p)==receipt['files'][str(p)]
  boxes=Counter()
  with mp.open('rb') as f:
   assert f.read(8)==b'RCATT001'
   while True:
    raw=f.read(256)
    if not raw:break
    assert len(raw)==256;a=struct.unpack('<32Q',raw);assert a[1]<=t
    if a[0]==1:boxes[(a[1],a[2])+tuple(x-(1<<64) if x>=1<<63 else x for x in a[10:16])]+=1
  assert sum(boxes.values())==row['attempts'];folder=D/c;folder.mkdir(parents=True);gp=folder/'actual_boxes.jsonl'
  with gp.open('x') as f:
   for key,n in sorted(boxes.items()):f.write(json.dumps(dict(phase=key[0],net=key[1],box=list(key[2:]),attempts=n),separators=(',',':'))+'\n')

  out=folder/'margin_candidates.jsonl';assert not out.exists();cp=subprocess.run([str(B),str(src),str(t),str(out)],capture_output=True,text=True);assert cp.returncode==0,cp.stderr;record_count,accepted=map(int,cp.stdout.split());assert accepted==old[row['case']]['tag_counts'][0]
  for p in [rp,mp,ep,gp,out]:bindings[str(p)]=sha(p)
  rows.append(dict(case=c,status='ACTUAL_SCOPE_AND_MARGIN_INPUTS_FROZEN',ready_iteration=t,boxes=str(gp),margins=str(out),margin_records=record_count,prefix_accepted_events=accepted,unique_phase_NET_boxes=len(boxes)));print('ATTEMPT_SCOPE_MARGIN_FROZEN',c,record_count,accepted,len(boxes),flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 (D/'frozen_inputs.json').write_text(json.dumps(dict(status='ACTUAL_SCOPE_AND_EXACT_MARGIN_INPUTS_FROZEN_NO_LABELS',rows=rows,bindings=bindings,final_labels_read=False),indent=2)+'\n')
if __name__=='__main__':main()
