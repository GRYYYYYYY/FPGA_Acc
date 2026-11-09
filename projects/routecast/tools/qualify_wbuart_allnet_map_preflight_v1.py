import json,hashlib
from pathlib import Path
from run_wbuart_allnet_map_case_v1 import execute
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_allnet_map_preflight_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);old=E/'wbuart_map_probe_targets_v1_2026-10-20/manifest.json';base=json.loads(old.read_text());receipt=R/'build/wbuart_allnet_map_query_v1_2026-10-20/receipt.json';br=json.loads(receipt.read_text());assert all(sha(p)==h for p,h in br['bindings'].items());assert sha(br['binary'])==br['binary_sha256'];cases=[]
 for enabled in [False,True]:
  row=dict(base['cases'][0]);row['case']='w096/episode_01/'+('on' if enabled else 'off');row['output']=str(D/('on' if enabled else 'off'));row['command']=[br['binary'],*row['command'][1:]];row['allmap_enabled']=enabled;cases.append(row)
 base['cases']=cases;base['bindings']={str(p):sha(p) for p in [old,receipt,Path(__file__),R/'tools/run_wbuart_allnet_map_case_v1.py',Path(br['binary'])]};manifest=D/'manifest.json';manifest.write_text(json.dumps(base,indent=2)+'\n');results=[]
 for row in cases:
  result=execute(manifest,row['case']);assert result['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS',result;results.append(result);print(row['case'],'FULL_PASS',flush=True)
 for name in ['output.route','owner_trace.tsv','expected_cost.tsv']:assert sha(D/'off'/name)==sha(D/'on'/name)==sha(Path(cases[0]['reference_output'])/name) if name!='expected_cost.tsv' else sha(D/'off'/name)==sha(D/'on'/name)
 for key in ['native_work','iterations','wirelength','diagnostic_cpd_ns']:assert results[0][key]==results[1][key]
 (D/'verification.json').write_text(json.dumps({'status':'PREFLIGHT_ON_OFF_FULL_AUDIT_AND_BYTE_WORK_PARITY_PASS','results':results,'bindings':{str(manifest):sha(manifest),str(D/'on/allmap.bin'):sha(D/'on/allmap.bin')},'query_adapter_qualification_pending':True},indent=2)+'\n');print('ALLNET_PREFLIGHT_PASS')
if __name__=='__main__':main()
