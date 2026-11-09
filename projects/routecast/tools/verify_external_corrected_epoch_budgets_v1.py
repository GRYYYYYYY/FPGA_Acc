"""Independent integer recomputation of all warm budgets from fresh native source."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_corrected_native_epoch_v1_2026-10-19';OLD=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 terminal=read(D/'preparation_terminal.json');sourceproof=D/'source_checkpoint/independent_xml_verification_v1.json';proof=read(sourceproof);assert all(sha(k)==h for k,h in proof['bindings'].items());source=read(D/'source_checkpoint/initial.json');oldsource=read(OLD/'source_checkpoints/w160/initial.json');ss={q['connection_id']:q for q in source['records']};os={q['connection_id']:q for q in oldsource['records']};assert ss.keys()==os.keys();source_delay_changes=sum(ss[c]['answer']['delay']!=os[c]['answer']['delay'] for c in ss);source_path_changes=sum(ss[c]['answer']['physical_edge_ids']!=os[c]['answer']['physical_edge_ids'] for c in ss);bindings={str(D/'preparation_terminal.json'):sha(D/'preparation_terminal.json'),str(sourceproof):sha(sourceproof),str(D/'source_checkpoint/initial.json'):sha(D/'source_checkpoint/initial.json'),str(OLD/'source_checkpoints/w160/initial.json'):sha(OLD/'source_checkpoints/w160/initial.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for case in terminal['cases']:
  methods={};row=dict(case=case['case']);warm=Path(case['warm']);scale=source['scale'];assert scale==10**18
  for method in ('raw_min','native_retained'):
   vp=warm/method/'verification.json';v=read(vp);assert all(sha(k)==h for k,h in v['bindings'].items());fp=warm/method/'initial.json';frame=read(fp);records={q['connection_id']:q for q in frame['records']};assert records.keys()==ss.keys();changed=up=down=anchored=0
   old=read(OLD/'predictions'/case['case']/'warm'/method/'initial.json');oldrows={q['connection_id']:q for q in old['records']}
   for cid,q in records.items():
    prior=ss[cid];assert prior['net_id']==q['net_id'];same=(prior['source'],prior['sink'])==(q['source'],q['sink']);floor=q['floor_integer'];proxy=max((scale+10**9-1)//10**9,(3*floor+1)//2);budget=max(proxy,prior['answer']['delay']) if same else proxy
    assert q['proxy_budget_integer']==proxy and q['budget_integer']==budget;assert q['answer']['delay']<=budget
    anchored+=same and prior['answer']['delay']>proxy;before=oldrows[cid]['budget_integer'];changed+=before!=budget;up+=budget>before;down+=budget<before
   methods[method]=records;row[method]=dict(checked_CIDs=len(records),new_source_anchored_budgets=anchored,budgets_changed_vs_original_epoch=changed,budgets_increased=up,budgets_decreased=down)
   for p in (vp,fp,OLD/'predictions'/case['case']/'warm'/method/'initial.json'):bindings[str(p)]=sha(p)
  assert all(methods['raw_min'][cid]['budget_integer']==methods['native_retained'][cid]['budget_integer'] for cid in ss);row['two_methods_budget_vectors_exact_equal']=True;rows.append(row);print(json.dumps(row),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'budget_epoch_verification_v1.json').write_text(json.dumps(dict(status='ALL3_BOTH_METHODS_93696_SOURCE_ANCHORED_BUDGETS_RECOMPUTED',source_connections=len(ss),source_raw_delays_changed=source_delay_changes,source_edge_paths_changed=source_path_changes,rows=rows,bindings=bindings,scope='Fresh corrected-native source controls every current budget. Raw/native matched budgets checked independently; graph-only floors and presearch timing reuse audited separately. Original epoch not replaced. No forecast score or native utility/full paid timing claim.'),indent=2)+'\n')
if __name__=='__main__':main()
