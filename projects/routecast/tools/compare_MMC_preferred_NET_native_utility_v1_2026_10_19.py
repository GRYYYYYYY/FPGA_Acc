"""Frozen all-case integer-work/QoR decision, requiring both full trace proofs."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 owner=R/'experiments/mmc_preferred_NET_owner_replay_v1_2026-10-19/verification.json';conn=R/'experiments/mmc_preferred_NET_connection_replay_v1_2026-10-19/verification.json';raw=R/'experiments/mmc_preferred_NET_connection_replay_v1_2026-10-19/independent_raw_verification_v1.json'
 assert json.loads(owner.read_text())['status']=='all3_preferred_NET_native_traces_independently_replayed'
 c=json.loads(conn.read_text());assert c['status']=='ALL3_CURRENT_CID_EXPLICIT_HEAP_WORK_REPLAY_PASS';assert json.loads(raw.read_text())['status']=='ALL3_INDEPENDENT_RAW_CID_VECTORS_PASS'
 protocol=R/'experiments/mmc_preferred_NET_native_utility_protocol_v1_2026-10-19/protocol.json';spec=json.loads(protocol.read_text());rows=[];keys=['NET_operations','connection_operations','heap_pushes','heap_pops'];bindings={str(p):sha(p) for p in [owner,conn,raw,protocol,Path(__file__).resolve()]}
 for job in spec['jobs']:
  case=job['case'];work=next(x for x in c['rows'] if x['case']==case);native=Path(job['cwd'])/'verification.json';v=json.loads(native.read_text());assert v['all_native_physical_and_canonical_pass'];n=v['rows'][0]
  zero=Path(job['zero_reference'])/'equivalence.json';z=json.loads(zero.read_text())['row'];baseline=dict(zip(keys,[z['preferred_scope_count'],z['successful_sink_operations'],z['attributed_heap_pushes'],z['attributed_heap_pops']]))
  nonreg={k:work[k]<=baseline[k] for k in keys};strict={k:work[k]<baseline[k] for k in keys};wire=n['wirelength']<=z['wirelength'];cpd=n['diagnostic_cpd_ns']<=z['CPD_ns']+1e-12
  rows.append({'case':case,'zero_work':baseline,'preferred_work':{k:work[k] for k in keys},'work_nonregression':nonreg,'work_strict_improvement':strict,'zero_wirelength':z['wirelength'],'preferred_wirelength':n['wirelength'],'wire_nonregression':wire,'diagnostic_CPD_nonregression':cpd,'primary_component_gate_pass':all(nonreg.values()) and any(strict.values()) and wire and cpd})
  for p in [native,zero]:bindings[str(p)]=sha(p)
 O=R/'experiments/mmc_preferred_NET_native_utility_review_v1_2026-10-19';O.mkdir(exist_ok=False)
 (O/'research_decision_v1.json').write_text(json.dumps({'status':'ALL3_FROZEN_NATIVE_COMPONENT_COMPARISONS_COMPLETE','cases':rows,'all3_primary_component_gate_pass':all(x['primary_component_gate_pass'] for x in rows),'bindings':bindings,'candidate_promoted':False,'full_workflow_gain_proven':False,'unseen_family_gain_proven':False,'hardware_gain_proven':False,'scope':'Exposed MMC component result; diagnostic CPD is not actual setup closure; complete continuous costs and original prediction quality remain separate requirements.'},indent=2)+'\n')
 print('PREFERRED_ALL3_GATE',all(x['primary_component_gate_pass'] for x in rows))
if __name__=='__main__':main()
