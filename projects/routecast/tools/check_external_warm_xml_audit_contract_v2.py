"""Native-kernel warm integration fixture; graph-context loader is substituted."""
import json,sys,tempfile,subprocess,hashlib,shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET
import prepare_external_warm_initializers_v1 as warm
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d)+'\n')
with tempfile.TemporaryDirectory() as tmp:
 root=Path(tmp);source=root/'source';source.mkdir();graph=root/'graph.xml';net=root/'net.xml';net.write_text('synthetic fixture')
 kinds=['SOURCE','CHANX','SINK','SINK','SINK'];edgepairs=[(0,1),(1,2),(1,3),(1,4)]
 graph.write_text('<rr_graph><switches><switch id="0" type="mux"><timing R="0" Tdel="1e-9"/></switch></switches><rr_nodes>'+''.join(f'<node id="{i}" type="{t}" capacity="1"><timing R="0" C="0"/></node>' for i,t in enumerate(kinds))+'</rr_nodes><rr_edges>'+''.join(f'<edge src_node="{u}" sink_node="{v}" switch_id="0"/>' for u,v in edgepairs)+'</rr_edges></rr_graph>')
 route=root/'source.route';route.write_text('Net 0 (n)\nNode: 0 SOURCE Switch: 0\nNode: 1 CHANX Switch: 0\nNode: 2 SINK Switch: -1\nNode: 1 CHANX Switch: 0\nNode: 3 SINK Switch: -1\n')
 oldq=[dict(connection_id=i,net_id=0,source=0,sink=i+2) for i in range(2)]
 newq=[dict(q) for q in oldq];newq[1]['sink']=4
 inputs={k:dict(path=str(p),sha256=sha(p)) for k,p in [('graph',graph),('net',net)]}
 ep=root/'source.json';target=root/'target.json'
 for p,qs in [(ep,oldq),(target,newq)]:write(p,dict(graph_sha256=sha(graph),inputs=inputs,net_names={'0':'n'},connections=qs))
 def floors(directory,qs):
  directory.mkdir(exist_ok=True);fl=directory/'floors.jsonl';fl.write_text(''.join(json.dumps(dict(q,minimum_integer=2*10**9))+'\n' for q in qs));fp=directory/'verification.json';write(fp,dict(status='ALL_FRAME_RAW_FLOORS_ORIGIN_PROOFS_NEW_MINIMA_AND_CURRENT_XML_PATHS_VERIFIED',graph_sha256=sha(graph),unreachable=0,bindings={str(fl):sha(fl)}));return fp,fl
 sf,sfl=floors(root/'source_floors',oldq);tf,tfl=floors(root/'target_floors',newq)
 initial=source/'initial.json';write(initial,dict(scale=10**18,graph_sha256=sha(graph),records=[dict(q,answer=dict(status='FOUND',physical_edge_ids=[0,i+1],delay=2*10**9),floor_integer=2*10**9,proxy_budget_integer=3*10**9,budget_integer=3*10**9) for i,q in enumerate(oldq)],ledger={'0':1,'1':1,'2':1,'3':1},independent_connection_ledger={'0':2,'1':2,'2':1,'3':1},overflow_units=0,history={},epochs={'0':0},required_connections=2,completed_connections=2))
 write(source/'receipt.json',dict(status='COMPLETE_SOURCE_IMPORTED_INDEPENDENT_NATIVE_AUDIT_PENDING',source_endpoint=str(ep),source_route=str(route),floor_proof=str(sf),bindings={str(p):sha(p) for p in [ep,graph,net,route,sf,sfl,initial]}))
 audit=subprocess.run([sys.executable,str(R/'tools/verify_external_native_source_checkpoint_xml_v1.py'),str(source)],capture_output=True,text=True);assert audit.returncode==0,audit.stderr
 fields=dict(row_offsets=[0,1,4,4,4,4],dest_ranks=[1,2,3,4],edge_ids=[0,1,2,3],capacities=[1]*5)
 rc=SimpleNamespace(scale=10**18,increments=[10**9]*4,initial=lambda n:0)
 nodes=list(ET.parse(graph).getroot().find('rr_nodes'))
 # Only the graph loader is replaced. Budget rule, bound source auditor,
 # compiled raw Dijkstra, compiled retained initializer and producer run normally.
 with patch.object(warm,'load_endpoints',return_value=(graph,sha(graph),nodes,fields,rc,newq)):
  result=warm.prepare(target,source,tf,root/'warm')
 assert result==dict(dirty_nets=1,connections=2)
 for mode in ('raw_min','native_retained'):
  d=root/'warm'/mode;f=json.loads((d/'initial.json').read_text());by={r['connection_id']:r for r in f['records']}
  assert by[0]['answer']['physical_edge_ids']==[0,1] and by[1]['answer']['physical_edge_ids']==[0,3]
  assert f['ledger']=={'0':1,'1':1,'2':1,'4':1} and f['independent_connection_ledger']=={'0':2,'1':2,'2':1,'4':1}
  assert f['epochs']=={'0':1} and f['history']=={} and f['overflow_units']==0
  assert not (d/'verification.json').exists()
  r=json.loads((d/'receipt.json').read_text());assert all(sha(Path(p))==h for p,h in r['bindings'].items())
 events=json.loads((root/'warm/native_retained/initializer_events.json').read_text());assert events[0]['retained_connection_ids']==[0] and events[0]['repair_calls']==1 and not events[0]['whole_NET_fallback']
 audit_tool=R/'tools/verify_external_warm_initializers_xml_v1.py'
 audit_results=[]
 for mode in ('raw_min','native_retained'):
  d=root/'warm'/mode
  completed=subprocess.run([sys.executable,str(audit_tool),str(d)],capture_output=True,text=True)
  assert completed.returncode==0,completed.stderr
  proof=json.loads((d/'verification.json').read_text());assert proof['native_staged_state_independent_xml_pass'] and proof['connections']==2
  audit_results.append(dict(case=mode,accepted=True))
 with patch.object(warm,'load_endpoints',return_value=(graph,sha(graph),nodes,fields,rc,oldq)):
  unchanged_result=warm.prepare(ep,source,sf,root/'unchanged_warm')
 assert unchanged_result==dict(dirty_nets=0,connections=2)
 for mode in ('raw_min','native_retained'):
  d=root/'unchanged_warm'/mode
  completed=subprocess.run([sys.executable,str(audit_tool),str(d)],capture_output=True,text=True)
  assert completed.returncode==0,completed.stderr
  f=json.loads((d/'initial.json').read_text());assert f['records']==json.loads(initial.read_text())['records'] and f['epochs']=={'0':0}
  assert json.loads((d/'initializer_events.json').read_text())==[]
  audit_results.append(dict(case=mode+'_all_unchanged',accepted=True))
 for case in ('delay','budget','ledger','epoch','path','dirty_set','retained_event'):
  d=root/('corrupt_'+case);shutil.copytree(root/'warm/native_retained',d);(d/'verification.json').unlink()
  initial=d/'initial.json';f=json.loads(initial.read_text());events_path=d/'initializer_events.json';events=json.loads(events_path.read_text())
  if case=='delay':f['records'][1]['answer']['delay']+=1
  if case=='budget':f['records'][1]['budget_integer']+=1
  if case=='ledger':f['ledger']['1']=2
  if case=='epoch':f['epochs']['0']=0
  if case=='path':f['records'][1]['answer']['physical_edge_ids']=[0,2]
  if case=='retained_event':events[0]['retained_connection_ids']=[]
  write(initial,f);write(events_path,events)
  receipt=json.loads((d/'receipt.json').read_text())
  # Replace all original arm output bindings with this directory's files;
  # mutations must reach semantic checks, rather than failing only hashes.
  original=root/'warm/native_retained'
  receipt['bindings']={p:h for p,h in receipt['bindings'].items() if Path(p).parent!=original}
  for name in ('initial.json','initializer_events.json','floors.json','history.json'):
   receipt['bindings'][str(d/name)]=sha(d/name)
  if case=='dirty_set':receipt['dirty_nets']=[]
  write(d/'receipt.json',receipt)
  completed=subprocess.run([sys.executable,str(audit_tool),str(d)],capture_output=True,text=True)
  assert completed.returncode!=0,case
  assert not (d/'verification.json').exists(),case
  audit_results.append(dict(case=case,accepted=False))
 out=R/'experiments/prospective_external_family_warm_xml_audit_contract_v2_2026-10-19';out.mkdir(exist_ok=False)
 write(out/'verification.json',dict(status='TWO_CHANGED_AND_TWO_UNCHANGED_ARMS_AND7_REBOUND_WARM_XML_NEGATIVES_PASS',audit_results=audit_results,bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/prepare_external_warm_initializers_v1.py',audit_tool]},raw_and_retained_ledgers_and_budgets_match=True,unchanged_connection_retained=True,changed_connection_repaired=True,zero_history_and_dirty_epoch_checked=True,scope='Synthetic audited source, real native search kernels and full producer. Graph-context loader substituted. Independent target XML audit executed on both fixture arms plus semantic negatives. No real design warm-state execution; graph loader substituted; full workflow remains unfrozen.'))
 print('WARM_INITIALIZER_NATIVE_INTEGRATION_FIXTURE_PASS')
