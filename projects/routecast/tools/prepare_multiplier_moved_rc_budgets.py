"""Exact same-placement witness budgets; no user clock or native STA claim."""
import json,shutil
from pathlib import Path
from fractions import Fraction
from prepared_csr import read
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_moved_rc_budgets_2026-10-06';out.mkdir();bindings={};reports=[]
shutil.copyfile(Path(__file__),out/'source.py')
for w in range(4,10):
 name=f'mult_{w}x{w}';context=base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name
 for folder in (context,base/'multiplier_family_length_switch_csr_2026-10-06'/name,base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset',base/'multiplier_moved_incremental_search_2026-10-06'/name,base/'multiplier_placement_swap_2026-10-06'/name):
  for p in folder.rglob('*'):
   if p.is_file():bindings[str(p)]=sha(p)
 predpaths=[base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/prediction.json',base/'multiplier_moved_incremental_search_2026-10-06'/name/'prediction.json'];preds=[json.loads(p.read_text()) for p in predpaths];graph=preds[0]['physical_graph_sha256'];assert all(p['physical_graph_sha256']==graph for p in preds)
 m,f=read(base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr',graph);rc=ExactBufferedRC(f,*load(context,graph));integer=IntegerRC(rc);dest=out/name;dest.mkdir()
 for step,pred in enumerate(preds):
  rows=[]
  for r in pred['connections']:
   d=rc.path(r['source'],r['sink'],r['physical_edge_ids']);v=integer.path(r['source'],r['sink'],r['physical_edge_ids']);assert Fraction(v,integer.scale)==d
   rows.append({k:r[k] for k in ('connection_id','net_id','source','sink')}|{'exact_delay_s':[d.numerator,d.denominator],'scaled_integer_budget':v})
  p=dest/f'step_{step}_budgets.json';p.write_text(json.dumps(rows)+'\n');reports.append({'design':name,'step':step,'connections':len(rows),'integer_scale':integer.scale,'reference_prediction_sha256':sha(predpaths[step]),'budget_sha256':sha(p)});print(reports[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'steps':reports,'scope':'Exact Fraction/integer witness budgets for initial and one archived compatible layout swap per design, cw300 graph. Does not reuse cw32 electrical context. No independent rawXML RC budget audit yet; no user clock/STA, route admissibility or incremental transaction claim.'},indent=2)+'\n')
