"""All9 synthetic RR vectors -> frozen components -> full setup reference -> native outputs."""
import csv,json,hashlib,struct,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from nominal_component_timing_bridge_v1 import NominalComponentTimingBridge
E=R/'experiments';C=E/'prospective_external_family_delay_components_v1_2026-10-19';BASE=E/'prospective_external_family_clock_constraints_v1_2026-10-19';MAP=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';D=E/'prospective_external_family_component_timing_bridge_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def bits(v):return struct.pack('>f',float(v)).hex()
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def main():
 proof=read(C/'verification.json');assert all(sha(k)==h for k,h in proof['bindings'].items());D.mkdir(exist_ok=False);bindings={str(C/'verification.json'):sha(C/'verification.json'),str(R/'tools/nominal_component_timing_bridge_v1.py'):sha(R/'tools/nominal_component_timing_bridge_v1.py'),str(R/'tools/native_setup_reference_v1.py'):sha(R/'tools/native_setup_reference_v1.py'),str(R/'tools/load_native_clock_constraints_v1.py'):sha(R/'tools/load_native_clock_constraints_v1.py'),str(Path(__file__).resolve()):sha(__file__)}
 (D/'protocol.json').write_text(json.dumps(dict(cases=[dict(case=r['case'],mode=r['mode']) for r in proof['rows']],bindings=bindings,acceptance='All actual updated native max/min edge weights and all atom/cluster slack/criticality bits match. Reference receives original nominal graph/components plus RR matrix vector only, no updated edge weights.',scope='Nominal fixed-packing model, synthetic RR vectors; no physical IPIN remap/route, generic STA or forecast quality claim.'),indent=2)+'\n');results=[]
 for r in proof['rows']:
  case,mode=r['case'],r['mode'];out=C/case/mode;component=C/case/'scaled/components_before.tsv';mp=MAP/case/'external_edge_CID_bindings_v1.json';bridge=NominalComponentTimingBridge(BASE/case,component,read(mp));updated=table(out/'updated_connections.tsv');RR={(int(q['net']),int(q['pin'])):float(q['delay_s']) for q in updated};edge_table={int(q['edge']):q for q in table(out/'timing_edges.tsv')}
  for scope,col in [('MAX','value_max_or_setup_s'),('MIN','value_min_or_hold_s')]:
   predicted=bridge.edge_weights(RR,scope);assert all(bits(value)==bits(edge_table[eid][col]) for eid,value in predicted.items())
  begin=time.perf_counter();ref=bridge.analyze(RR);atoms=table(out/'timing_atoms.tsv');groups=defaultdict(list);bad_atoms=[]
  for a in atoms:
   if not a['raw_criticality']:continue
   n=int(a['external_node']);slack=min(ref['slacks'][n].values());crit=ref['criticality'][n];groups[int(a['native_net']),int(a['local_pin'])].append((slack,crit))
   if bits(slack)!=bits(a['setup_slack_s']) or bits(crit)!=bits(a['raw_criticality']):bad_atoms.append(int(a['atom_pin']))
  bad_connections=[]
  for q in updated:
   key=int(q['net']),int(q['pin']);values=groups[key]
   if bits(min(s for s,c in values))!=bits(q['slack_s']) or bits(max(c for s,c in values))!=bits(q['criticality']):bad_connections.append(list(key))
  # Invalid-domain inputs must be rejected before any baseline state can be modified.
  invalid=dict(RR);invalid.pop(next(iter(invalid)))
  try:bridge.edge_weights(invalid)
  except ValueError:pass
  else:raise AssertionError('partial vector accepted')
  invalid=dict(RR);invalid[next(iter(invalid))]=-1.
  try:bridge.edge_weights(invalid)
  except ValueError:pass
  else:raise AssertionError('negative delay accepted')
  result=dict(case=case,mode=mode,edge_reconstruction_checks=len(predicted)*2,atom_records=sum(len(v) for v in groups.values()),atom_mismatches=len(bad_atoms),connection_aggregates=len(updated),connection_mismatches=len(bad_connections),invalid_partial_and_negative_inputs_rejected=True,reference_seconds=time.perf_counter()-begin);results.append(result);print(json.dumps(result),flush=True)
  fp=D/case/mode;fp.mkdir(parents=True);(fp/'mismatches.json').write_text(json.dumps(dict(atoms=bad_atoms,connections=bad_connections))+'\n')
  for p in [component,mp,out/'updated_connections.tsv',out/'timing_edges.tsv',out/'timing_atoms.tsv',fp/'mismatches.json']:bindings[str(p)]=sha(p)
 assert all(sha(k)==h for k,h in bindings.items());passed=all(r['atom_mismatches']==r['connection_mismatches']==0 for r in results);(D/'verification.json').write_text(json.dumps(dict(status='ALL9_RR_TO_COMPONENT_EDGE_TO_SETUP_NATIVE_EXACT_FLOAT32_PASS' if passed else 'COMPONENT_BRIDGE_NATIVE_SETUP_MISMATCH',passed=passed,rows=results,bindings=bindings,scope='No perturbed native graph weights used as model input. Frozen original nominal components plus changed RR vectors reproduce native outputs. Still not invariance after placement or physical pin remap, physical route legality, dynamic forecast quality or total paid time acceptance.'),indent=2)+'\n');sys.exit(0 if passed else 1)
if __name__=='__main__':main()
