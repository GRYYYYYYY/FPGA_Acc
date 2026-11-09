"""Audit all12 fullRR pressure arms, native outcomes and exact NET2 CHANNEL support."""
import json,re,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_early_net_trace_v1 import verify
from analyze_external_early_net_response_v1 import load
from verify_external_initial_response_observer_source_v1 import trees
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_full_rr_pressure_factorial_v1_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';C=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 terminal=read(D/'terminal.json');assert terminal['status']=='ALL12_FROZEN_FULL_RR_PRESSURE_FACTORIAL_ARMS_TERMINAL' and len(terminal['rows'])==12;protocol=read(D/'protocol.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());cases={r['case']:r for r in read(D/'manifest.json')['cases']};source=load(I/'source/early_net_trace.tsv');bindings={str(D/'terminal.json'):sha(D/'terminal.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'manifest.json'):sha(D/'manifest.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for item in terminal['rows']:
  case,arm=item['case'],item['arm'];c=cases[case+'/'+arm];folder=Path(c['output']);proof=folder/'verification.json';audit=read(proof);assert all(sha(p)==h for p,h in audit['bindings'].items());assert audit['status']==item['status'];row=dict(case=case,arm=arm,status=audit['status'],native_success=audit['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS')
  bindings[str(proof)]=sha(proof)
  if not row['native_success']:
   row['error']=audit.get('error');rows.append(row);continue
  trace=load(folder/'early_net_trace.tsv');original=load(I/case/'early_net_trace.tsv');assert trace[2,2]['B']==original[2,2]['B'] and trace[2,2]['C']==original[2,2]['C'];assert all(trace[k]==original[k] for k in original if k[0]==1 or k==(2,85));log=(folder/'native.log').read_text();applied=re.findall(r'^RC_PRESSURE_APPLIED channels=(\d+) modified=(\d+)$',log,re.M);restored=re.findall(r'^RC_PRESSURE_RESTORED modified=(\d+)$',log,re.M);assert len(applied)==len(restored)==1;assert sha(folder/'pressure.tsv')==sha(c['inputs']['pressure']);modified=0;count=0
  for line in (folder/'pressure.tsv').open():
   n,a,b=map(int,line.split());assert n==count;count+=1;modified+=a!=b
  assert count==129090==int(applied[0][0]) and modified==int(applied[0][1])==int(restored[0]);replay=verify(folder,c['endpoint']);a=set(trace[2,2]['A']);b=set(original[2,2]['A']);s=set(source[2,2]['A']);same=trees(folder/'output.route')==trees(I/case/'output.route');assert same==item['final_tree_identical_to_original'];row.update(pressure_nodes=count,modified_pressure_nodes=modified,replay=replay,NET2_after2_CHANNEL_diff_to_original=len(a^b),NET2_after2_CHANNEL_diff_to_source=len(a^s),final_printed_route_identical_to_original=same)
  if arm=='channel_0_nonchannel_0':assert modified==0 and same and trace==original
  if arm in ['channel_0_nonchannel_0','channel_1_nonchannel_0']:
   oldarm='own_pressure' if arm=='channel_0_nonchannel_0' else 'source_pressure';old=C/case/oldarm/'native';row['old_channel_arm_early_trace_identical']=sha(folder/'early_net_trace.tsv')==sha(old/'early_net_trace.tsv');row['old_channel_arm_iteration_trace_identical']=sha(folder/'iteration_support.tsv')==sha(old/'iteration_support.tsv');bindings[str(old/'early_net_trace.tsv')]=sha(old/'early_net_trace.tsv');bindings[str(old/'iteration_support.tsv')]=sha(old/'iteration_support.tsv')
  for p in [folder/'early_net_trace.tsv',folder/'iteration_support.tsv',folder/'output.route',folder/'pressure.tsv',folder/'native.log',I/case/'early_net_trace.tsv',I/case/'output.route']:bindings[str(p)]=sha(p)
  rows.append(row);print(json.dumps(row),flush=True)
 bindings[str(I/'source/early_net_trace.tsv')]=sha(I/'source/early_net_trace.tsv');assert all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='ALL12_FULL_RR_FACTORIAL_OUTCOMES_AND_RESTORED_OBSERVED_CHANNEL_REPLAY_VERIFIED',rows=rows,bindings=bindings,scope='Runtime guard validates every RR expected input; restored CHANNEL occupancy replay checked independently. Full nonCHANNEL dynamic after-call occupancy not independently exported; native final physical/canonical checked for successes. NET2 after2 comparison is CHANNEL support only. No final-label inference, predictor acceptance, native utility or matched speedup claim.'),f,indent=2)
if __name__=='__main__':main()
