"""Replay orchestration against archived real backend results, no new search."""
import json
from pathlib import Path
from collections import defaultdict
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from free_pin_budget_selection import choose
from pre_route_endpoints import sha
out=Path('experiments/alu4_free_pin_selection_contract_2026-10-05');assert not out.exists();root=Path('experiments/alu4_free_pin_budget_trial_2026-10-05');g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');catalog=PinChoiceCatalog(g);before=json.loads(Path('experiments/alu4_whole_net_budget_cohort_2026-10-05/prediction.json').read_text());rows={r['connection_id']:r for r in before['connections']};users=defaultdict(set)
for cid,r in rows.items():w=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);users[r['sink'],w['selected_ipin_ptc']].add(cid)
eq={r['cid']:r for r in json.loads(Path('experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json').read_text())['checks']};reports=json.loads((root/'receipt.json').read_text())['reports'];attempts=json.loads((root/'query_candidates.json').read_text());calls=0;replayed=[]
class Replay:
 def __init__(self,old,opin,results):self.catalog=catalog;self.old=old;self.opin=opin;self.results={r['selected_ipin_ptc']:r for r in results};self.seen=[]
 def query_prepared(self,context,source,sink,source_ptc,target,budget,overrides,forbidden,max_labels):
  assert (source,sink,source_ptc)==(self.old['source'],self.old['sink'],self.opin);r=self.results[target];assert budget==r['budget'] and max_labels==r['max_labels'];self.seen.append(target);return r
for report,attempt in zip(reports,attempts):
 cid=report['cid'];assert cid==attempt['cid'];old=rows[cid];w=catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);engine=Replay(old,w['selected_opin_ptc'],attempt['targets']);occupied={ptc for (sink,ptc),ids in users.items() if sink==old['sink'] and ids};r=choose(engine,None,old['source'],old['sink'],w['selected_opin_ptc'],w['selected_ipin_ptc'],report['budget'],eq[cid]['physical_members'],occupied,max_labels=report['max_labels']);assert r['selection_complete'] and r['status']=='FOUND';assert engine.seen==sorted(engine.results);best=r['best']
 for key,value in best.items():
  if key!='path':assert report[key]==value
 if report['committed']:
  pin=best['selected_ipin_ptc'];users[old['sink'],w['selected_ipin_ptc']].remove(cid);users[old['sink'],pin].add(cid);rows[cid]={**old,'physical_edge_ids':best['path']}
 calls+=len(engine.seen);replayed.append(cid)
assert len(replayed)==90 and calls==1791
out.mkdir();(out/'selector.py').write_bytes(Path('tools/free_pin_budget_selection.py').read_bytes());(out/'source.py').write_bytes(Path(__file__).read_bytes());record={'selector_sha256':sha(out/'selector.py'),'source_sha256':sha(out/'source.py'),'archived_query_candidates_sha256':sha(root/'query_candidates.json'),'queries_replayed':90,'target_backend_results_replayed':calls,'all_targets_and_selected_results_equal':True,'scope':'Orchestration replay of archived1791 actual backend outcomes; no fresh search, performance, whole-net or native timing claim'};(out/'receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record),flush=True)
