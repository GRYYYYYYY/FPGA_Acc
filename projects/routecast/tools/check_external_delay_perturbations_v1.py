"""All9 float32 matrix perturbation and exact updated-edge setup recurrence contracts."""
import json,csv,hashlib,struct,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from native_setup_reference_v1 import SetupReference,f32
E=R/'experiments';D=E/'prospective_external_family_delay_perturbations_v1_2026-10-19';BASE=E/'prospective_external_family_clock_constraints_v1_2026-10-19';MAP=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';B=R/'build/native_external_delay_perturbations_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def bits(v):return struct.pack('>f',float(v)).hex()
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def main():
 t=read(D/'terminal.json');p=read(D/'protocol.json');assert len(t['rows'])==9 and all(r['exit_code']==0 and r['marker'] and r['no_route_generated'] and r['initial_connection_bytes_equal'] for r in t['rows']);assert all(sha(k)==h for k,h in p['bindings'].items());bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(R/'tools/native_setup_reference_v1.py'):sha(R/'tools/native_setup_reference_v1.py'),str(R/'tools/load_native_clock_constraints_v1.py'):sha(R/'tools/load_native_clock_constraints_v1.py'),str(Path(__file__).resolve()):sha(__file__)}
 (D/'comparison_protocol.json').write_text(json.dumps(dict(cases=[r['case'] for r in t['rows']],acceptance='All9 matrix transformations and exact float32 atom/cluster slack+criticality matches on actual updated native edge weights. No tolerance tuning. Typed graph topology, constraints and atom mapping remain fixed. Only mapped external data edges may change.',bindings=bindings,scope='Delay-only nominal mapping fixtures. Recurrence validation, not frozen-offset mapping or physical route/quality acceptance.'),indent=2)+'\n');rows=[]
 for r in t['rows']:
  case,mode=r['case'].rsplit('/',1);out=D/r['case'];base=BASE/case;original={(int(q['net']),int(q['pin'])):q for q in table(out/'initial_connections.tsv')};changes=table(out/'delay_changes.tsv');updated={(int(q['net']),int(q['pin'])):q for q in table(out/'updated_connections.tsv')};assert len(changes)==len(original)==len(updated)==15616;changed=set()
  for q in changes:
   key=int(q['net']),int(q['pin']);before=f32(q['before_s']);assert bits(before)==bits(original[key]['delay_s']);after=f32(q['after_s']);expected=f32(before*1.25) if mode=='scaled' else f32(before+f32(.25e-9)) if mode=='sparse_plus' and key[0]%17==0 else 0. if mode=='sparse_zero' and key[0]%29==0 else before;assert bits(expected)==bits(after)==bits(updated[key]['delay_s']);assert all(updated[key][k]==original[key][k] for k in ['source_rr','sink_rr'])
   if before!=after:changed.add(key)
  assert changed;mapping=read(MAP/case/'external_edge_CID_bindings_v1.json');allowed={q['edge'] for q in mapping if (q['native_net_id'],q['local_sink_pin']) in changed};oldedges={q['edge']:q for q in table(base/'timing_edges.tsv')};newedges={q['edge']:q for q in table(out/'timing_edges.tsv')};assert oldedges.keys()==newedges.keys();changed_edges=[]
  for eid,a in oldedges.items():
   b=newedges[eid];assert all(a[k]==b[k] for k in ['source','sink','type','disabled']);assert a['value_min_or_hold_s']==b['value_min_or_hold_s']
   if bits(a['value_max_or_setup_s'])!=bits(b['value_max_or_setup_s']):assert int(eid) in allowed;changed_edges.append(int(eid))
  for name in ['timing_nodes.tsv','clock_constraints.tsv']:assert sha(out/name)==sha(base/name)
  atoms=table(out/'timing_atoms.tsv');oldatoms=table(base/'timing_atoms.tsv');assert len(atoms)==len(oldatoms)
  for a,b in zip(atoms,oldatoms):assert all(a[k]==b[k] for k in ['atom_pin','atom','port','bit','external_node','internal_node','native_net','local_pin'])
  begin=time.perf_counter();ref=SetupReference(out).analyze();groups=defaultdict(list);bad_atoms=[];count=0
  for a in atoms:
   if not a['raw_criticality']:continue
   node=int(a['external_node']);slack=min(ref['slacks'][node].values());crit=ref['criticality'][node];groups[int(a['native_net']),int(a['local_pin'])].append((slack,crit));count+=1
   if bits(slack)!=bits(a['setup_slack_s']) or bits(crit)!=bits(a['raw_criticality']):bad_atoms.append(dict(pin=int(a['atom_pin']),node=node,reference_slack=slack,native_slack=float(a['setup_slack_s']),reference_crit=crit,native_crit=float(a['raw_criticality'])))
  assert groups.keys()==updated.keys();bad_connections=[]
  for key,values in groups.items():
   if bits(min(a for a,b in values))!=bits(updated[key]['slack_s']) or bits(max(b for a,b in values))!=bits(updated[key]['criticality']):bad_connections.append(key)
  mismatch=out/'reference_mismatches.json';mismatch.write_text(json.dumps(dict(atoms=bad_atoms,connections=bad_connections),indent=2)+'\n');rows.append(dict(case=case,mode=mode,changed_native_pin_delays=len(changed),changed_external_timing_edges=len(changed_edges),atom_records=count,atom_mismatches=len(bad_atoms),connection_aggregates=len(groups),connection_mismatches=len(bad_connections),reference_seconds=time.perf_counter()-begin));print(json.dumps(rows[-1]),flush=True)
  for name in ['initial_connections.tsv','delay_changes.tsv','updated_connections.tsv','timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv','reference_mismatches.json']:fp=out/name;bindings[str(fp)]=sha(fp)
  for name in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv']:fp=base/name;bindings[str(fp)]=sha(fp)
  fp=MAP/case/'external_edge_CID_bindings_v1.json';bindings[str(fp)]=sha(fp)
 assert all(sha(k)==h for k,h in bindings.items());passed=all(r['atom_mismatches']==r['connection_mismatches']==0 for r in rows);(D/'verification.json').write_text(json.dumps(dict(status='ALL9_DELAY_ONLY_NATIVE_SETUP_REFERENCE_EXACT_FLOAT32_PASS' if passed else 'DELAY_ONLY_SETUP_REFERENCE_MISMATCH_REQUIRES_DIAGNOSIS',passed=passed,rows=rows,bindings=bindings,scope='Actual updated native edge weights input to independent full setup recurrence. All9 fixed, nominal topology and pin mapping constant. Does not prove RR path-to-edge offset invariance, physical route legality, general timing corner coverage, feedback quality or speedup.'),indent=2)+'\n');sys.exit(0 if passed else 1)
if __name__=='__main__':main()
