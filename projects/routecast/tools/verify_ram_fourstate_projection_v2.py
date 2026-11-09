"""Verify four-state contract traces, proof receipts and seven actual group geometries."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_fourstate_projection_v2_2026-10-21';H=E/'ram_fourstate_contract_xsim_v1_2026-10-21';P=E/'parmys_source_provenance_replay_v1_2026-10-21';C=E/'shallow_ram_address_completion_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for root in [D,H]:
  for p,h in json.loads((root/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 stages=json.loads((H/'results.json').read_text())['rows'];assert len(stages)==3 and all(r['exit_code']==0 for r in stages);log=(H/'xsim.log').read_text();assert 'ORIGINAL_RAM_FOURSTATE_CONTRACT_ALL256_PASS' in log;cases=[s.split(',')[1:] for s in log.splitlines() if s.startswith('FOURSTATE_CASE,')];assert len(cases)==256;seen=set()
 for ac,wc,dc,l,p,e in cases:
  ac,wc,dc=map(int,[ac,wc,dc]);seen.add((ac,wc,dc));hi,lo=divmod(ac,4);expect='x' if hi>=2 or lo>=2 else ('01xz'[dc] if wc==1 else str(lo));assert l.lower()==p.lower()==e.lower()==expect
 assert seen=={(a,w,d) for a in range(16) for w in range(4) for d in range(4)}
 tb=(H/'tb.v').read_text();assert 'logical_ram.Mem[i] !== expected[i]' in tb and 'physical_ram.Mem[i] !== expected[i]' in tb and "physical_ram.Mem[1024] !== 1'bx" in tb
 rows=json.loads((D/'results.json').read_text())['rows'];assert len(rows)==12
 for row in rows:
  f=D/f'a{row["address_bits"]}_{row["mode"]}';text=(f/'yosys.log').read_text();assert 'Found and reported 0 problems.' in text
  if row['mode']=='state_read_frame':assert row['exit_code']==0 and row['proof_passed'] and 'no model found: SUCCESS' in text
  else:assert row['exit_code']==1 and row['proof_failed'] and 'proof did fail' in text
 observed=json.loads((E/'ram_read_port_observability_v1_2026-10-21/results.json').read_text())['rows'];eligible={r['instance'] for r in observed if r['source']=='mkDelayWorker32B' and r['cross_port_read_is_unused']};assert len(eligible)==7;prov=next(r for r in json.loads((P/'verification_v1.json').read_text())['rows'] if r['source']=='mkDelayWorker32B');design=json.loads((C/'mkDelayWorker32B/candidate.json').read_text())['modules']['mkDelayWorker32B'];groups=[]
 for g in prov['groups']:
  if g['source_instance'] not in eligible:continue
  a=g['address_bits'];assert a in [2,3,4];lanes=[design['cells'][n] for n in g['descendant_cells']];assert len(lanes)==g['data_bits'];sample=lanes[0]['connections']
  for cell in lanes:
   z=cell['connections'];assert cell['type']=='dual_port_ram' and z['we2']==['0'] and len(z['data1'])==1
   for p in ['clk','we1','addr1']:assert z[p]==sample[p]
   assert len(z['addr1'])==11 and z['addr1'][a:]==['0']*(11-a)
  groups.append({'instance':g['source_instance'],'address_bits':a,'observed_output':'out1','unobserved_output':'out2','lanes':len(lanes),'initial_correspondence_required':True})
 assert len(groups)==7 and sum(g['lanes'] for g in groups)==824
 files=[H/'tb.v',H/'xsim.log',D/'results.json',P/'verification_v1.json',C/'mkDelayWorker32B/candidate.json',E/'ram_read_port_observability_v1_2026-10-21/results.json'];files += [D/f'a{r["address_bits"]}_{r["mode"]}'/'yosys.log' for r in rows]
 out={'status':'FOURSTATE_POINTWISE_RAM_RELATION_AND_7_GROUP_GEOMETRIES_VERIFIED','original_HDL_cases':256,'positive_SAT_proofs':3,'negative_controls_expected_failures':9,'eligible_groups':groups,'eligible_aux_read_bits':824,'total_aux_read_bits':1336,'remaining_cross_read_bits':512,'induction_argument':'Under matching initial row values, arbitrary tracked-row update equality implies all embedded rows stay related after each stable event; outside-row frame preserves unused physical rows. Correlated old read values at current known row follow from the all-row relation; own-port output equality follows. Unknown address read X/write ignored and X/Z enables nonwriting match finite original HDL guard checks.','scope':'Explicit four-valued behavioral recurrence, conditional initial state relation and post-settle primitive observation. Actual seven groups match geometry/own-port observability; full word input/output provenance and same-clock downstream scheduling are not proven by this lemma. Does not qualify two used cross-read words or complete source/physical/packing equivalence.','bindings':{str(p.relative_to(R)):sha(p) for p in files}};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
