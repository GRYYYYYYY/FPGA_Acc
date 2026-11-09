"""Synthetic admission stubs exercise case evaluator joins, not routing proofs."""
import copy,json,tempfile,hashlib
from pathlib import Path
from evaluate_external_forecast_case_v1 import evaluate
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d)+'\n')
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);graph=d/'graph.xml';graph.write_text('synthetic graph identity only')
 ep=d/'endpoints.json';q=dict(connection_id=0,net_id=0,source=3,sink=4)
 write(ep,dict(graph_sha256=sha(graph),inputs={'graph':dict(path=str(graph),sha256=sha(graph))},connections=[q]))
 resources=d/'resources.jsonl';resources.write_text(''.join(json.dumps(dict(id=n,capacity=1,bins=[[0,n%2,0,'CHANX',0]]))+'\n' for n in range(3)))
 bins=d/'spatial_bins.json';write(bins,[dict(key=[0,0,0,'CHANX',0],capacity=2),dict(key=[0,1,0,'CHANX',0],capacity=1)])
 domain=d/'domain.json';write(domain,dict(graph_sha256=sha(graph),graph_nodes=5,resources=3,resource_k=1,spatial_bins=2,spatial_k=1,bindings={str(p):sha(p) for p in (resources,bins,graph)}))
 independent=d/'independent.json';write(independent,dict(status='ALL3_EXPAT_RESOURCE_IDENTITIES_INCLUSIVE_BINS_CAPACITIES_AND_K_EXACT',bindings={str(domain):sha(domain)}))
 frames={};proofs={}
 for name,node in [('previous_native',1),('raw_min_on',1),('native_retained_on',0)]:
  frame=d/(name+'.json');write(frame,dict(graph_sha256=sha(graph),completed_connections=1,required_connections=1,records=[q],ledger={str(node):1}));frames[name]=frame
  proof=d/(name+'_proof.json');write(proof,dict(status='SOURCE_XML_FRACTION_PATH_BUDGET_LEDGER_AUDIT_PASS',all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,bindings={str(frame):sha(frame),str(ep):sha(ep)}));proofs[name]=proof
 physical=d/'physical.json';write(physical,dict(inputs_sha256={'graph':sha(graph)},overflow_units=0,node_occupancy={'0':1}))
 label=d/'label.json';write(label,dict(status='FULL_PHYSICAL_AND_CANONICAL_PASS',case='synthetic',canonical={'semantic_consistency_gate_pass':True},bindings={str(physical):sha(physical)}))
 spec=dict(schema='ROUTECAST_EXTERNAL_FORECAST_CASE_V1',case='synthetic',endpoint=str(ep),domain_proof=str(domain),domain_independent_proof=str(independent),source_proof=str(proofs['previous_native']),source_frame=str(frames['previous_native']),predictions={n:dict(frame=str(frames[n]),proof=str(proofs[n])) for n in ('raw_min_on','native_retained_on')},label_proof=str(label),label_physical_audit=str(physical))
 sp=d/'spec.json';write(sp,spec);assert evaluate(sp,d/'comparison.json') is True
 outcomes=[]
 original_label=label.read_text();original_domain=domain.read_text();original_proof=proofs['native_retained_on'].read_text()
 for case in ('wrong_label_case','incomplete_prediction_proof','uncertified_frame','wrong_target_epoch','wrong_graph_domain'):
  label.write_text(original_label);domain.write_text(original_domain);proofs['native_retained_on'].write_text(original_proof)
  if case=='wrong_label_case':v=json.loads(label.read_text());v['case']='other';write(label,v)
  if case=='incomplete_prediction_proof':v=json.loads(original_proof);v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']=False;write(proofs['native_retained_on'],v)
  if case=='uncertified_frame':v=json.loads(original_proof);v['bindings'].pop(str(frames['native_retained_on']));write(proofs['native_retained_on'],v)
  if case=='wrong_target_epoch':v=json.loads(original_proof);v['bindings'].pop(str(ep));write(proofs['native_retained_on'],v)
  if case=='wrong_graph_domain':v=json.loads(original_domain);v['graph_sha256']='b'*64;write(domain,v);write(independent,dict(status='ALL3_EXPAT_RESOURCE_IDENTITIES_INCLUSIVE_BINS_CAPACITIES_AND_K_EXACT',bindings={str(domain):sha(domain)}))
  try:evaluate(sp,d/(case+'.json'))
  except ValueError:outcomes.append(case)
  else:raise AssertionError(case)
 out=R/'experiments/prospective_external_family_forecast_case_contract_v1_2026-10-19';out.mkdir(exist_ok=False)
 paths=[Path(__file__).resolve(),R/'tools/evaluate_external_forecast_case_v1.py',R/'tools/external_forecast_metrics_v1.py']
 write(out/'verification.json',dict(status='SYNTHETIC_CASE_SUCCESS_AND5_ADMISSION_JOIN_REJECTIONS_PASS',bindings={str(p):sha(p) for p in paths},negative_contracts=outcomes,scope='Synthetic admission stubs and toy graph identity, testing evaluator IO/evidence joins and metric execution only. No actual route/canonical proof, independent graph parser or real external case admitted by these fixtures.'))
 print('CASE_EVALUATOR_SUCCESS_AND5_REJECTIONS_PASS')
