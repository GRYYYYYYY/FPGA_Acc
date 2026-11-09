"""Fresh same-binary replacement arm exactly reproduces previous diagnostic arm."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from replay_prince_native_sources_v1 import sequences
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_reactive_floor_trial_v1_2026-10-20';OLD=R/'experiments/prince_final_other_oracle_trial_v1_2026-10-20'
def main():
 p=D/'verification.json';op=OLD/'verification.json';new={x['case']:x for x in json.loads(p.read_text())['rows']};old={x['case']:x for x in json.loads(op.read_text())['rows']};bindings={str(q):sha(q) for q in [p,op,Path(__file__)]};rows=[]
 for case,row in new.items():
  if not case.endswith('/oracle'):continue
  prior=old[case];assert row['iterations']==prior['iterations'] and row['native_exit_code']==prior['native_exit_code'];a=D/case;b=OLD/case;assert sequences(a/'output.route')==sequences(b/'output.route')
  for name in ['queries.tsv','queries.tsv.connections.tsv','queries.tsv.ledger.bin']:
   ap=a/name;bp=b/name;h=sha(ap);assert h==row['files'][str(ap)]==sha(bp)==prior['files'][str(bp)];bindings[str(ap)]=h;bindings[str(bp)]=h
  rows.append(dict(case=case,iterations=row['iterations'],native_legal=row['native_full_check_pass'],cost_order_summary_and_connection_ledger_bytes_equal=True,physical_sequences_equal=True))
 assert len(rows)==6;out=D/'full_replacement_reproduction_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL6_FRESH_FULL_REPLACEMENT_ARMS_REPRODUCE',rows=rows,bindings=bindings),indent=2)+'\n');print('FULL_REPLACEMENT_REPRODUCTION_PASS',len(rows))
if __name__=='__main__':main()
