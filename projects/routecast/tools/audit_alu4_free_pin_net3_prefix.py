"""Full independent dynamic ownership, cost, budget and selection audit."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from buffered_delay_cost import BufferedDelayCost
from pre_route_endpoints import sha
root=Path('experiments/alu4_free_pin_cohort_2026-10-05');audit_out=Path('experiments/alu4_free_pin_cohort_net3_audit_2026-10-05');assert not audit_out.exists();protocol=json.loads((root/'protocol.json').read_text());checkpoint_files=sorted((root/'checkpoints').glob('*.json'),key=lambda p:int(p.stem));checkpoints=[json.loads(p.read_text()) for p in checkpoint_files if json.loads(p.read_text())['report']['net']==3];assert len(checkpoints)==88;receipt={'protocol_sha256':sha(root/'protocol.json'),'input_sha256':protocol['input_sha256'],'reports':[q['report'] for q in checkpoints]};assert all(sha(p)==h for p,h in receipt['input_sha256'].items())

g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');catalog=PinChoiceCatalog(g);model=BufferedDelayCost(g);before=json.loads(Path('experiments/alu4_free_pin_budget_trial_2026-10-05/prediction.json').read_text());rows={r['connection_id']:r for r in before['connections']};original=dict(rows);users=defaultdict(set)
for cid,r in rows.items():w=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);users[r['sink'],w['selected_ipin_ptc']].add(cid)
eq={r['cid']:r for r in json.loads(Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json').read_text())['checks']};attempts=[q['target_queries'] for q in checkpoints];reports=receipt['reports'];spans={}
for n,node in g.nodes.items():
 loc=dict(node.location);spans[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1 if node.type in {'CHANX','CHANY'} else 0
factor=(len(g.nodes)-1)*max(spans.values())+1;statuses=Counter();incomplete=0;repins=[]
assert len(attempts)==len(reports)==88
for report,attempt in zip(reports,attempts):
 cid=report['cid'];assert cid==attempt['cid'];old=rows[cid];w=catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);members=eq[cid]['physical_members'];targets={w['selected_ipin_ptc']}|({p for p in members if not users[old['sink'],p]} if eq[cid]['equivalent']=='full' else set());assert {q['selected_ipin_ptc'] for q in attempt['targets']}==targets
 built={g.edges[e].sink for r in rows.values() if r['net_id']==old['net_id'] and r['connection_id']!=cid for e in r['physical_edge_ids']};found=[];budget=sum(model.weights[e] for e in original[cid]['physical_edge_ids'])
 for q in attempt['targets']:
  assert q['status'] in {'FOUND','UNREACHABLE','LABEL_LIMIT'};statuses[q['status']]+=1;assert q['budget']==budget
  if q['status']=='FOUND':
   nw=catalog.witness(old['source'],old['sink'],q['path']);assert nw['selected_ipin_ptc']==q['selected_ipin_ptc'] and nw['selected_opin_ptc']==w['selected_opin_ptc'];assert sum(model.weights[e] for e in q['path'])==q['delay']<=budget
   cost=sum(spans[g.edges[e].sink]*(1 if g.edges[e].sink in built else factor+1) for e in q['path']);assert cost==q['cost'];found.append(q)
 limited=any(q['status']=='LABEL_LIMIT' for q in attempt['targets']);assert attempt['selection_complete']==report['selection_complete']==(not limited);incomplete+=limited
 if report['status']=='FOUND':
  best=min(found,key=lambda q:(q['cost'],q['delay'],q['selected_ipin_ptc']));assert (report['cost'],report['delay'],report['selected_ipin_ptc'])==(best['cost'],best['delay'],best['selected_ipin_ptc']);assert report['optimal_over_supplied_free_targets']==(not limited)
  if report['committed']:
   users[old['sink'],w['selected_ipin_ptc']].remove(cid);users[old['sink'],best['selected_ipin_ptc']].add(cid);rows[cid]={**old,'physical_edge_ids':best['path'],'method':'incremental_budget_free_pin_branch'}
   if w['selected_ipin_ptc']!=best['selected_ipin_ptc']:repins.append(cid)
 else:assert not found and not report['committed']
final=json.loads((root/'net_3_prediction.json').read_text());assert {r['connection_id']:r for r in final['connections']}==rows
r={'prediction_sha256':sha(root/'net_3_prediction.json'),'completed_net':3,'checkpoint_sha256':{str(p):sha(p) for p in checkpoint_files if int(p.stem) in {q['report']['cid'] for q in checkpoints}},'source_sha256':sha(__file__),'requests':88,'target_queries':sum(statuses.values()),'statuses':dict(statuses),'incomplete_selections':incomplete,'repinned_cids':repins,'all_found_path_cost_budget_and_dynamic_ownership_verified':True,'full_final_connection_records_reconstructed_exactly':True,'scope':'Independent completed-net3 prefix candidate accounting and exact checkpoint-state reconstruction; not full1012 cohort; no proof of UNREACHABLE or fresh native timing'};audit_out.mkdir();(audit_out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='repinned_cids'}),flush=True)
