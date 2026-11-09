"""Execute own replay controls first, source-pressure diagnostics only after all3 pass."""
import json,sys,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from run_external_pressure_native_case_v1 import execute
from verify_external_initial_response_observer_source_v1 import trees
E=R/'experiments';D=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19';B=R/'build/native_external_net2_pressure_intervention_v1_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');build=read(B/'receipt.json');contract=read(E/'net2_pressure_guard_contract_v1_2026-10-19/verification.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());assert all(sha(p)==h for p,h in build['bindings'].items());assert all(sha(p)==h for p,h in contract['bindings'].items());assert sha(build['binary'])==build['binary_sha256'];base=read(I/'target_manifest.json');cases=[]
 for arm in ['own_pressure','source_pressure']:
  for c in protocol['cases']:
   a=next(a for a in c['arms'] if a['arm']==arm);r=copy.deepcopy(c['original_manifest_case']);r['case']=c['case']+'/'+arm;r['command'][0]=build['binary'];r['inputs']['pressure']=a['pressure'];r['output']=a['native_output'];cases.append(r)
 base['cases']=cases;base['bindings'].update(protocol['bindings']);base['bindings'].update(build['bindings']);base['bindings'].update({str(D/'protocol.json'):sha(D/'protocol.json'),build['binary']:build['binary_sha256'],str(Path(__file__).resolve()):sha(__file__),str(R/'tools/run_external_pressure_native_case_v1.py'):sha(R/'tools/run_external_pressure_native_case_v1.py')});mp=D/'manifest.json'
 with mp.open('x') as f:json.dump(base,f,indent=2)
 results=[]
 for r in cases:
  out=execute(mp,r['case']);original_case=r['case'].rsplit('/',1)[0];arm=r['case'].rsplit('/',1)[1];folder=Path(r['output']);log=(folder/'native.log').read_text();assert log.count('RC_PRESSURE_APPLIED ')==log.count('RC_PRESSURE_RESTORED ')==1;baseline=I/original_case;identical=trees(folder/'output.route')==trees(baseline/'output.route');row=dict(case=original_case,arm=arm,status=out['status'],final_tree_identical_to_original=identical)
  if arm=='own_pressure':assert out['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS' and identical and read(folder/'physical_audit.json')['node_occupancy']==read(baseline/'physical_audit.json')['node_occupancy']
  results.append(row);print(json.dumps(row),flush=True)
  with (D/('receipt_'+original_case.replace('/','_')+'_'+arm+'.json')).open('x') as f:json.dump(dict(result=row,verification=str(folder/'verification.json')),f,indent=2)
 with (D/'terminal.json').open('x') as f:json.dump(dict(status='ALL6_FIXED_PRESSURE_INTERVENTION_ARMS_TERMINAL',rows=results,scope='Source-pressure sensitivity only. Own3 controls identical. Native failures retained, no forecast quality promotion.'),f,indent=2)
if __name__=='__main__':main()
