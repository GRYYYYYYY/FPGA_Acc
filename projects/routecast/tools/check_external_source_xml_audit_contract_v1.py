"""Exercise XML auditor using a shared trunk and rebound semantic corruptions."""
import copy, hashlib, json, subprocess, sys, tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1]
AUDIT=R/'tools/verify_external_native_source_checkpoint_xml_v1.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x)+'\n')
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);graph=root/'graph.xml';route=root/'design.route';ep=root/'endpoints.json';fp=root/'floor_proof.json';fl=root/'floors.jsonl'
 graph.write_text('<rr_graph><switches><switch id="0" type="mux"><timing R="0" Tdel="1e-9"/></switch></switches><rr_nodes>'+''.join(f'<node id="{i}" type="{t}" capacity="1"><timing R="0" C="0"/></node>' for i,t in enumerate(['SOURCE','CHANX','SINK','SINK']))+'</rr_nodes><rr_edges>'+''.join(f'<edge src_node="{u}" sink_node="{v}" switch_id="0"/>' for u,v in [(0,1),(1,2),(1,3)])+'</rr_edges></rr_graph>')
 route.write_text('Net 0 (n)\nNode: 0 SOURCE Switch: 0\nNode: 1 CHANX Switch: 0\nNode: 2 SINK Switch: -1\nNode: 1 CHANX Switch: 0\nNode: 3 SINK Switch: -1\n')
 qs=[dict(connection_id=i,net_id=0,source=0,sink=i+2) for i in range(2)]
 write(ep,dict(graph_sha256=sha(graph),inputs={'graph':dict(path=str(graph),sha256=sha(graph))},connections=qs,net_names={'0':'n'}))
 fl.write_text(''.join(json.dumps(dict(q,minimum_integer=2*10**9))+'\n' for q in qs));write(fp,dict(graph_sha256=sha(graph),unreachable=0,bindings={str(fl):sha(fl)}))
 frame=dict(scale=10**18,graph_sha256=sha(graph),records=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[0,i+1],delay=2*10**9),floor_integer=2*10**9,proxy_budget_integer=3*10**9,budget_integer=3*10**9) for i,q in enumerate(qs)],ledger={'0':1,'1':1,'2':1,'3':1},independent_connection_ledger={'0':2,'1':2,'2':1,'3':1},overflow_units=0,history={},epochs={'0':0},required_connections=2,completed_connections=2)
 outcomes=[]
 for case in ['valid','wrong_edge','wrong_delay','wrong_budget','connection_not_NET_ledger','missing_CID','wrong_floor']:
  d=root/case;d.mkdir();f=copy.deepcopy(frame)
  if case=='wrong_edge':f['records'][1]['answer']['physical_edge_ids']=[0,1]
  if case=='wrong_delay':f['records'][0]['answer']['delay']+=1
  if case=='wrong_budget':f['records'][0]['budget_integer']+=1
  if case=='connection_not_NET_ledger':f['ledger']['1']=2
  if case=='missing_CID':f['records'].pop()
  if case=='wrong_floor':f['records'][0]['floor_integer']+=1
  initial=d/'initial.json';write(initial,f)
  # Rebind corruptions so tests must reach semantic checks, not hash guards.
  bindings={str(p):sha(p) for p in [ep,graph,route,fp,fl,initial]}
  write(d/'receipt.json',dict(status='COMPLETE_SOURCE_IMPORTED_INDEPENDENT_NATIVE_AUDIT_PENDING',source_endpoint=str(ep),source_route=str(route),floor_proof=str(fp),bindings=bindings))
  result=subprocess.run([sys.executable,str(AUDIT),str(d)],capture_output=True,text=True)
  assert (result.returncode==0)==(case=='valid'),(case,result.stderr)
  outcomes.append(dict(case=case,returncode=result.returncode,expected_rejection=case!='valid'))
 out=R/'experiments/prospective_external_family_source_xml_audit_contract_v1_2026-10-19';out.mkdir(exist_ok=False)
 write(out/'verification.json',dict(status='SHARED_TRUNK_POSITIVE_AND6_REBOUND_SEMANTIC_NEGATIVES_PASS',cases=outcomes,bindings={str(p):sha(p) for p in [AUDIT,Path(__file__).resolve()]},scope='Synthetic two-CID shared-trunk XML audit only. Does not certify real source route or producer end-to-end. Shared route-format parser scope retained.'))
 print('XML_AUDIT_CONTRACT_PASS',len(outcomes))
