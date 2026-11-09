"""Audit six frozen pressure arms, restored-state replay and exact NET2 support."""
import json,re,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_early_net_trace_v1 import verify
from analyze_external_early_net_response_v1 import load
from verify_external_initial_response_observer_source_v1 import trees
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 terminal=read(D/'terminal.json');assert terminal['status']=='ALL6_FIXED_PRESSURE_INTERVENTION_ARMS_TERMINAL' and len(terminal['rows'])==6;protocol=read(D/'protocol.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());manifest=read(D/'manifest.json');cases={r['case']:r for r in manifest['cases']};source=load(I/'source/early_net_trace.tsv');rows=[];bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'manifest.json'):sha(D/'manifest.json'),str(Path(__file__).resolve()):sha(__file__)}
 for item in terminal['rows']:
  case,arm=item['case'],item['arm'];c=cases[case+'/'+arm];folder=Path(c['output']);audit=read(folder/'verification.json');assert all(sha(p)==h for p,h in audit['bindings'].items());assert audit['status']==item['status'];assert sha(folder/'pressure.tsv')==sha(c['inputs']['pressure']);trace=load(folder/'early_net_trace.tsv');original=load(I/case/'early_net_trace.tsv');log=(folder/'native.log').read_text();applied=re.findall(r'^RC_PRESSURE_APPLIED channels=(\d+) modified=(\d+)$',log,re.M);restored=re.findall(r'^RC_PRESSURE_RESTORED modified=(\d+)$',log,re.M);assert len(applied)==len(restored)==1;pressure=[tuple(map(int,x.split())) for x in (folder/'pressure.tsv').read_text().splitlines()];changes=sum(a!=b for n,a,b in pressure);assert len(pressure)==protocol['channels']==int(applied[0][0]) and changes==int(applied[0][1])==int(restored[0]);assert trace[2,2]['B']==original[2,2]['B'] and trace[2,2]['C']==original[2,2]['C'];assert all(trace[k]==original[k] for k in original if k[0]==1 or k==(2,85));replay=verify(folder,c['endpoint']);a=set(trace[2,2]['A']);b=set(original[2,2]['A']);s=set(source[2,2]['A']);same_final=trees(folder/'output.route')==trees(I/case/'output.route');assert same_final==item['final_tree_identical_to_original']
  if arm=='own_pressure':assert changes==0 and audit['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and same_final and trace==original
  row=dict(case=case,arm=arm,status=audit['status'],replay=replay,pressure_channels=len(pressure),changed_pressure_CHANNELs=changes,NET2_after2_support_symmetric_difference_to_original=len(a^b),NET2_after2_support_symmetric_difference_to_source=len(a^s),NET2_after2_support_size=len(a),final_route_identical_to_original=same_final);rows.append(row)
  for p in [folder/'verification.json',folder/'early_net_trace.tsv',folder/'pressure.tsv',folder/'output.route',folder/'native.log',I/case/'early_net_trace.tsv',I/case/'output.route']:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 bindings[str(I/'source/early_net_trace.tsv')]=sha(I/'source/early_net_trace.tsv');assert all(sha(p)==h for p,h in bindings.items())
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_PRESSURE_ARMS_PRESTATE_RESTORED_OCCUPANCY_REPLAY_AND_NET2_SUPPORT_VERIFIED',rows=rows,bindings=bindings,scope='Source-pressure diagnostic changes CHANNEL demand jointly inconsistent with other stored trees during native NET call; verified restored observed nodes and native final physical/canonical. Not calibrated predictor, original case gate, native improvement or speedup. NET2 comparison concerns CHANNEL support only, not identical all-node/switch tree.'),f,indent=2)
if __name__=='__main__':main()
