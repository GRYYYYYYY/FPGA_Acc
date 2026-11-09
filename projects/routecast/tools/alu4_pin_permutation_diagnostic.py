"""Evaluator-only pin multiset mismatch and unused interchangeable capacity."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from pre_route_endpoints import sha
out=Path('experiments/alu4_pin_permutation_diagnostic_2026-10-05');assert not out.exists();files={'prediction':'experiments/alu4_whole_net_budget_cohort_2026-10-05/prediction.json','native':'experiments/alu4_transfer_evaluation_2026-10-05/native_audit.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml','equivalence':'experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json'};inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);c=PinChoiceCatalog(g);pred=json.loads(Path(files['prediction']).read_text());native=json.loads(Path(files['native']).read_text());checks=json.loads(Path(files['equivalence']).read_text())['checks'];groups=[]
def pins(rows,key):
 result=defaultdict(Counter)
 for r in rows:
  w=c.witness(r['source'],r['sink'],r[key]);result[r['net_id'],r['sink']][w['selected_ipin_ptc']]+=1
 return result
p=pins(pred['connections'],'physical_edge_ids');b=pins(native['connections'],'edge_ids');assert set(p)==set(b)
occupied=defaultdict(set)
for (net,sink),values in p.items():occupied[sink].update(values)
for key in sorted(p):groups.append({'net':key[0],'sink':key[1],'prediction_ptcs':dict(p[key]),'native_ptcs':dict(b[key]),'same_multiset':p[key]==b[key]})
classes={r['sink_class']:r for r in checks};free=[{'sink_class':sink,'equivalent':r['equivalent'],'occupied_ptcs':len(occupied[sink]),'free_ptcs':sorted(set(r['physical_members'])-occupied[sink])} for sink,r in sorted(classes.items())];summary={'endpoint_groups':len(groups),'different_pin_multiset_groups':sum(not r['same_multiset'] for r in groups),'full_equivalence_classes_with_free_pins':sum(r['equivalent']=='full' and bool(r['free_ptcs']) for r in free),'free_full_equivalence_pins':sum(len(r['free_ptcs']) for r in free if r['equivalent']=='full')};assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'groups.json').write_text(json.dumps(groups)+'\n');(out/'free_classes.json').write_text(json.dumps(free)+'\n');r={'summary':summary,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'Posthoc permutation multiset and free capacity accounting; not per-atom pin identity or proof permutation causes span gap; native labels not candidate inputs'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(summary),flush=True)
