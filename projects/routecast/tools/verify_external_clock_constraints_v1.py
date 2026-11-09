"""Independent range-to-getter constraint resolution; exact prior snapshot parity."""
import csv,json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from load_native_clock_constraints_v1 import load,resolve,value,serializable
E=R/'experiments';D=E/'prospective_external_family_clock_constraints_v1_2026-10-19';BASE=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';B=R/'build/native_external_clock_constraints_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 p=read(D/'protocol.json');assert all(sha(k)==h for k,h in p['bindings'].items());t=read(D/'terminal.json');assert len(t['rows'])==3 and all(r['exit_code']==0 and r['marker'] and r['no_route_generated'] and r['initial_connection_bytes_equal'] for r in t['rows']);bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'terminal.json'):sha(D/'terminal.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/load_native_clock_constraints_v1.py'):sha(R/'tools/load_native_clock_constraints_v1.py')};rows=[]
 for c in t['rows']:
  case=c['case'];out=D/case;native=BASE/case
  for name in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','initial_connections.tsv']:
   assert sha(out/name)==sha(native/name);bindings[str(out/name)]=sha(out/name);bindings[str(native/name)]=sha(native/name)
  cp=out/'clock_constraints.tsv';d=load(cp);nodes={int(r['node']):int(r['type']) for r in csv.DictReader((out/'timing_nodes.tsv').open(),delimiter='\t')};sinknodes={n for n,t in nodes.items() if t==1};domains=set(d['domains']);assert all(row['source']==-1 or row['source'] in nodes for row in d['domains'].values());assert all(n in nodes for n in d['constants']);seen=set()
  for (kind,src,sink,capture),v in d['clock_constraints'].items():assert src in domains and sink in domains and (capture==-1 or capture in sinknodes)
  for (kind,delay,node,domain),v in d['io_constraints'].items():assert node in nodes and domain in domains
  for q in d['native_queries']:
   key=q['source'],q['sink'],q['capture'];assert key not in seen;seen.add(key);assert resolve(d,*key)=={k:q[k] for k in ['setup','hold','analyze']}
  assert seen=={(src,sink,node) for src in domains for sink in domains for node in sinknodes|{-1}}
  for q in d['native_latency_queries']:assert q['value']==d['latencies'].get((q['kind'],q['domain']),value('0'))
  for q in d['native_uncertainty_queries']:
   for mode in ['SETUP','HOLD']:assert q[mode.lower()]==d['uncertainties'].get((mode,q['source'],q['sink']),value('0'))
  machine=out/'clock_constraints.json';machine.write_text(json.dumps(serializable(d),indent=2)+'\n');bindings[str(cp)]=sha(cp);bindings[str(machine)]=sha(machine);rows.append(dict(case=case,domains=len(domains),domain_names=[r['name'] for r in d['domains'].values()],clock_constraints=len(d['clock_constraints']),io_constraints=len(d['io_constraints']),constant_generators=len(d['constants']),resolved_capture_queries=len(seen),uncertainty_queries=len(d['native_uncertainty_queries']),source_latency_queries=len(d['native_latency_queries']),native_getter_resolution_exact=True,all_prior_graph_atom_and_initial_files_byte_equal=True));print(json.dumps(rows[-1]),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_MACHINE_CLOCK_CONSTRAINTS_NATIVE_RESOLUTION_AND_SNAPSHOT_PARITY_VERIFIED',rows=rows,bindings=bindings,scope='Machine-readable ranges/defaults validated against native getters at every current SINK and domainpair. Current cohort one clock/no capture-specific overrides; synthetic coverage and full required-time/criticality recurrence remain separate. No speculative pin-offset invariance or dynamic STA acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
