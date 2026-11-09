"""Same-placement complete cohort budgets, exact integer/Fraction/oracle parity."""
import json,shutil
from pathlib import Path
from fractions import Fraction
from prepared_csr import read
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from pre_route_endpoints import sha

root=Path(__file__).resolve().parents[1];base=root/'experiments'
out=base/'adder_tree_online_move_rc_budgets_2026-10-06';out.mkdir();(out/'sources').mkdir()
for n in ['prepare_online_move_rc_budgets.py','csr_exact_buffered_rc.py','integer_rc_context.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py']:
 shutil.copyfile(root/'tools'/n,out/'sources'/n)
context=base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits'
quality=base/'adder_tree_online_dynamic_net_quality_2026-10-06';qr=json.loads((quality/'receipt.json').read_text())
graph=json.loads((base/'adder_tree_2L032_move_sequence_2026-10-06/protocol.json').read_text())['inputs']['rr_graph']
m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',graph['sha256'])
rc=ExactBufferedRC(f,*load(context,graph['sha256']));integer=IntegerRC(rc)
protocol={'graph_sha256':graph['sha256'],'context_receipt_sha256':sha(context/'receipt.json'),'quality_receipt_sha256':sha(quality/'receipt.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Fixed same-placement constant predictor delay per CID at initial+3 real moves; exact integer buffered search applies only to authenticated buffered Cinternal0 graph. Not user clock/native STA or cross-placement baseline budget.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
for q in qr['results']:
 k=int(q['design'].split('_')[1]);predfile=base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if k==0 else base/'adder_tree_2L032_move_sequence_audit_2026-10-06'/f'step_{k}_prediction.json'
 assert sha(predfile)==q['reference_prediction_sha256'];pred=json.loads(predfile.read_text());metricfile=quality/q['design']/'connections.json';assert sha(metricfile)==q['connection_report_sha256'];metrics={r['connection_id']:r for r in json.loads(metricfile.read_text())}
 rows=[]
 for r in pred['connections']:
  d=rc.path(r['source'],r['sink'],r['physical_edge_ids']);assert d==Fraction(metrics[r['connection_id']]['old_rc_s_exact']);v=integer.path(r['source'],r['sink'],r['physical_edge_ids']);assert Fraction(v,integer.scale)==d
  rows.append({k:r[k] for k in ('connection_id','net_id','source','sink')}|{'exact_delay_s':[d.numerator,d.denominator],'scaled_integer_budget':v})
 path=out/f'step_{k}_budgets.json';path.write_text(json.dumps(rows,indent=2)+'\n');report={'step':k,'connections':len(rows),'reference_prediction_sha256':sha(predfile),'oracle_report_sha256':sha(metricfile),'budget_sha256':sha(path)};reports.append(report);print(json.dumps(report),flush=True)
assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'integer_scale':integer.scale,'steps':reports,'all_2064_baseline_budgets_match_independent_xml_rc':True},indent=2)+'\n')
