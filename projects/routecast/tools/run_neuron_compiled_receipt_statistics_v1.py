"""Complete compiled receipt statistics under bounded address space."""
import datetime,json,resource,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_complete_model_receipt_summary_v1 import summarize
from observe_neuron_compiled_pipeline_v1 import snapshot
case=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
assert json.loads((case/'model_terminal.json').read_text())['exit_status']==0
s=snapshot();free=s['shared_headroom_bytes'];limit=512*2**20;reserve=8*2**30 if not s['pipeline_terminal']['observed'] else 0
admission=dict(shared_headroom_bytes=free,child_limit_bytes=limit,original_pipeline_reservation_bytes=reserve,margin_bytes=8*2**30,admitted=free>=limit+reserve+8*2**30)
if not admission['admitted']:raise RuntimeError('Statistics not launched: insufficient memory')
resource.setrlimit(resource.RLIMIT_AS,(limit,limit));tick=time.perf_counter()
summary=summarize(case/'model/receipt.json')
assert len(summary['rounds'])==2 and all(x['events']==50767 for x in summary['rounds'])
old=json.loads((R/'experiments/neuron_certified_native_metrics_v1_2026-10-15/model_cost_attribution.json').read_text())
ratios={k:summary['timers'][k]/v for k,v in old['timers'].items() if k in summary['timers'] and v>0}
result=dict(bindings={**closure([Path(__file__)]),str(case/'model/receipt.json'):sha(case/'model/receipt.json'),str(case/'model_terminal.json'):sha(case/'model_terminal.json')},checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),resource_admission=admission,summary=summary,compiled_work=json.loads((case/'model/compiled_primary_work.json').read_text()),old_model_timer_ratios=ratios,search_share_of_resident=summary['timers']['search_seconds']/summary['timers']['total_paid_resident_seconds'],paired_speedup_proven=False,all_independent_audits_completed=s['pipeline_terminal']['observed'],seconds=time.perf_counter()-tick,scope='Complete new receipt statistics and historical single-run timer ratios. No causal or paired speedup, final parity admission, hotspot improvement or full workflow gain claim.')
out=R/'experiments/neuron_compiled_receipt_statistics_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','summary')},indent=2),flush=True)
