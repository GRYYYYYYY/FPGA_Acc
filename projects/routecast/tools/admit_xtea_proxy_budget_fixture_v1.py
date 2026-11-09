"""Closed XTEA fixture admission with independent original-control rational budgets."""
import json,math,struct,hashlib
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17';model=out/'model';old=R/'experiments/xtea_scaled_present_factor1_pipeline_v1_2026-10-15/model'
 assert load(out/'pipeline_terminal.json')['all_stages_completed']
 bindings={}
 def bind(p):bindings[str(p)]=sha(p);return load(p)
 def merge(mapping):
  for p,h in mapping.items():assert p not in bindings or bindings[p]==h;bindings[p]=h
 for stage in ['model','initial_audit','sketch_audit','event_audit']:
  assert bind(out/(stage+'_terminal.json'))['exit_status']==0
  m=bind(out/(stage+'_process.json'));p=Path('/proc')/str(m['pid'])/'stat'
  if p.exists():assert p.read_text().rsplit(')',1)[1].split()[19]!=m['start_stat'].rsplit(')',1)[1].split()[19]
  assert m['address_space_limit_bytes']==2**30 and bind(out/(stage+'_admission.json'))['admitted']
 for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  v=bind(model/name);assert v['completed']==2450 and v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];merge(v['bindings'])
 event=load(model/'verification.json');assert event['events']==2896 and event['complete_primary_search_after_rejection_and_isolated_witnesses_pass']
 protocol=bind(model/'protocol.json');assert protocol['budget_policy']=='original_budget_plus_ceil_one_minus_criticality_times_floor_v1'
 cp=Path(protocol['criticality_input_proof']).parent/'initial_connection_criticalities.json';criticalities={x['connection_id']:Fraction(struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0]) for x in bind(cp)}
 initial=bind(model/'initial.json');control=bind(old/'initial.json');baseline={x['connection_id']:x for x in control['records']};changed=0
 for name in ['initial.json','sketch.json']:
  frame=bind(model/name);assert len(frame['records'])==len({x['connection_id'] for x in frame['records']})==2450
  for row in frame['records']:
   cid=row['connection_id'];o=baseline[cid];assert row['floor_integer']==o['floor_integer']
   expected=o['budget_integer']+math.ceil((1-criticalities[cid])*o['floor_integer']);assert row['budget_integer']==expected
   if name=='initial.json':changed+=expected!=o['budget_integer']
 for frame in [initial,control]:
  for row in frame['records']:row.pop('budget_integer')
 assert initial==control and sha(model/'floors.json')==sha(old/'floors.json')
 bindings[str(Path(__file__).resolve())]=sha(Path(__file__))
 assert all(sha(p)==h for p,h in bindings.items())
 result=dict(all_pass=True,completed=2450,events=2896,changed_budgets=changed,all_original_initial_paths_floor_and_ledgers_preserved=True,all_initial_and_final_budgets_independently_recomputed_from_control=True,final_overflow=event['overflow_units'],bindings=bindings,scope='XTEA exposed development integration fixture only; no neuron quality or native workflow gain.',promoted=False)
 with (out/'closed_admission_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
if __name__=='__main__':main()
