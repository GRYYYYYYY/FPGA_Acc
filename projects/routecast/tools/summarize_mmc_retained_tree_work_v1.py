"""Summarize certified recorded search work, without claiming paired speedup."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'experiments/mmc_retained_tree_full_schedule_v1_2026-10-13'
 bindings=closure([Path(__file__)])
 def load(p):
  bindings[str(p)]=sha(p);return json.loads(p.read_text())
 assert load(out/'pipeline_terminal.json')['all_stages_completed']
 proof=load(out/'model/verification.json')
 assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(p)==h for p,h in proof['bindings'].items());bindings.update(proof['bindings'])
 receipt=load(out/'model/receipt.json');rows=[]
 for round_ in receipt['rounds']:
  events=round_['events'];assert len(events)==55300
  calls=retained=fallback=0
  for e in events:
   ids=e['primary_search_connection_ids'];kept=e['retained_connection_ids']
   assert len(ids)==len(set(ids))==e['primary_search_calls']
   assert len(kept)==len(set(kept)) and not set(ids)&set(kept)
   calls+=len(ids);retained+=len(kept);fallback+=int('fallback' in e)
  rows.append(dict(round_index=round_['round_index'],nets=len(events),recorded_primary_search_calls=calls,retained_connections=retained,fallback_events=fallback,overflow_after=round_['overflow_after'],round_seconds=round_['seconds']))
 timing={k:receipt[k] for k in ['total_paid_resident_seconds','model_setup_seconds','initial_seconds','feedback_seconds','search_seconds','fallback_seconds','occupancy_context_seconds','ledger_check_seconds']}
 assert all(sha(p)==h for p,h in bindings.items())
 dest=out/'recorded_work_summary_v1.json';assert not dest.exists()
 dest.write_text(json.dumps(dict(bindings=bindings,rounds=rows,timing=timing,paired_speedup_proven=False,scope='Recorded primary API calls and independent event mask checks; fallback internal work separate, no independent execution trace or paired total speed proof.'),indent=2)+'\n')
 print(json.dumps(dict(rounds=rows,timing=timing)),flush=True)
if __name__=='__main__':main()
