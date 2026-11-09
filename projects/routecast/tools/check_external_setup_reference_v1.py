"""Frozen all3 exact-bit native atom and cluster setup baseline comparison."""
import csv,json,sys,hashlib,struct,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from native_setup_reference_v1 import SetupReference
E=R/'experiments';P=E/'prospective_external_family_clock_constraints_v1_2026-10-19';D=E/'prospective_external_family_setup_reference_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def bits(v):return struct.pack('>f',float(v)).hex()
def main():
 proof=read(P/'verification.json');assert all(sha(k)==h for k,h in proof['bindings'].items());D.mkdir(exist_ok=False);bindings={str(P/'verification.json'):sha(P/'verification.json'),str(R/'tools/native_setup_reference_v1.py'):sha(R/'tools/native_setup_reference_v1.py'),str(R/'tools/load_native_clock_constraints_v1.py'):sha(R/'tools/load_native_clock_constraints_v1.py'),str(Path(__file__).resolve()):sha(__file__)}
 (D/'protocol.json').write_text(json.dumps(dict(cases=[r['case'] for r in proof['rows']],bindings=bindings,acceptance='Exact float32 bits for every exported data-sink atom slack/criticality and every15616 cluster aggregate percase. No tolerance fitting.',scope='Independent Python full setup reference on current snapshots only. Explicit constants/multiple IO-domain unsupported rejection. No speculative pin-offset invariance, dynamic updates, forecast or general STA acceptance.'),indent=2)+'\n');rows=[]
 for c in proof['rows']:
  case=c['case'];folder=P/case;begin=time.perf_counter();result=SetupReference(folder).analyze();atoms=list(csv.DictReader((folder/'timing_atoms.tsv').open(),delimiter='\t'));mismatches=[];count=0;groups={}
  for a in atoms:
   if not a['raw_criticality']:continue
   node=int(a['external_node']);slack=min(result['slacks'][node].values());crit=result['criticality'][node];count+=1;key=(int(a['native_net']),int(a['local_pin']));g=groups.setdefault(key,dict(slack=slack,criticality=crit));g['slack']=min(g['slack'],slack);g['criticality']=max(g['criticality'],crit)
   if bits(slack)!=bits(a['setup_slack_s']) or bits(crit)!=bits(a['raw_criticality']):mismatches.append(dict(atom_pin=int(a['atom_pin']),node=node,reference_slack=slack,native_slack=float(a['setup_slack_s']),reference_criticality=crit,native_criticality=float(a['raw_criticality'])))
  payload=E/'prospective_external_family_frame_timings_v1_2026-10-19'/case/'initial_connection_criticalities.json';pm=[]
  for q in read(payload):
   g=groups[q['native_net_id'],q['local_sink_pin']]
   if bits(g['slack'])!=q['slack_bits'] or bits(g['criticality'])!=q['raw_criticality_bits']:pm.append(q['connection_id'])
  out=D/case;out.mkdir(parents=True);(out/'mismatches.json').write_text(json.dumps(dict(atoms=mismatches,connection_ids=pm),indent=2)+'\n');row=dict(case=case,data_sink_atoms=count,atom_mismatches=len(mismatches),connection_mismatches=len(pm),seconds=time.perf_counter()-begin,max_required={str(k):v for k,v in result['max_required'].items()},worst_slack={str(k):v for k,v in result['worst_slack'].items()});rows.append(row);print(json.dumps(row),flush=True)
  for name in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv']:p=folder/name;bindings[str(p)]=sha(p)
  bindings[str(payload)]=sha(payload);bindings[str(out/'mismatches.json')]=sha(out/'mismatches.json')
 assert all(sha(k)==h for k,h in bindings.items());passed=all(r['atom_mismatches']==r['connection_mismatches']==0 for r in rows);(D/'verification.json').write_text(json.dumps(dict(status='ALL3_SETUP_REFERENCE_EXACT_NATIVE_BASELINE_PASS' if passed else 'SETUP_REFERENCE_BASELINE_MISMATCH_REQUIRES_DIAGNOSIS',passed=passed,rows=rows,bindings=bindings,scope='Initial snapshot recurrence only, not dynamic forecast updates or complete general timing analyzer.'),indent=2)+'\n');sys.exit(0 if passed else 1)
if __name__=='__main__':main()
