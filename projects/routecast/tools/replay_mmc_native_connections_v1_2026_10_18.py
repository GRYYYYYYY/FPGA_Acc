"""Complete native-pin event universe; explicit-call RRR only, no CID inference."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from native_connection_trace_replay_v1 import replay
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';source=E/'mmc_native_connection_cascade_trace_v1_2026-10-18';rp=source/'cohort_equivalence.json';r=json.loads(rp.read_text());assert r['all6_native_full_output_bytes_integer_counters_equal'];core=E/'native_connection_trace_replay_core_v1_2026-10-18/verification.json';c=json.loads(core.read_text());assert c['status']=='strict_native_connection_trace_parser_core_fixtures_pass';out=E/'mmc_native_connection_replay_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={**r['bindings'],str(rp):sha(rp),str(core):sha(core),str(Path(__file__)):sha(__file__),str(R/'tools/native_connection_trace_replay_v1.py'):sha(R/'tools/native_connection_trace_replay_v1.py')};rows=[]
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for row in r['rows']:
   case,arm=row['case'],row['arm'];trace=source/case/arm/'connection_trace.tsv';assert sha(trace)==bindings[str(trace)];v=replay(trace);assert v['router_success'] and v['successful']==row['native_work']['total_rerouted_connection_operations'];assert len(v['iterations'])==row['native_work']['iterations'];assert all(x['native_counter_checked'] for x in v['iterations'])
   for a,b in zip(v['iterations'],row['native_work']['rows']):assert a['iteration']==b['iteration'] and a['successful']==b['rerouted_connection_operations']
   d=out/(case+'__'+arm);d.mkdir();(d/'native_NETs.json').write_text(json.dumps(v['nets'],separators=(',',':')));count=nonignored=0
   with (d/'native_sink_counts.jsonl').open('x') as f:
    for key,meta in sorted(v['pins'].items()):
     net,pin=key
     if pin==0:continue
     count+=1;nonignored+=not v['nets'][net]['ignored'];success=v['successful_operations'][key];failed=v['failed_attempts'][key];item=dict(native_NET=net,native_sink_index=pin,source_RR=v['pins'][net,0]['rr'],sink_RR=meta['rr'],initially_reached=meta['initially_reached'],native_ignored=v['nets'][net]['ignored'],successful_sink_operations=success,failed_sink_attempts=failed,observed_explicit_reroute=success>0 and (meta['initially_reached'] or success>1));f.write(json.dumps(item,separators=(',',':'))+'\n')
   summary={k:v[k] for k in ['attempts','successful','failed','distinct_successful_native_pins','distinct_initially_reached_successful_pins','distinct_repeated_native_pins']};summary.update(case=case,arm=arm,known_native_sink_pin_universe=count,nonignored_native_sink_pin_universe=nonignored,zero_success_pins=count-v['distinct_successful_native_pins'],iterations=v['iterations'],files={str(p):sha(p) for p in d.iterdir() if p.is_file()},manifest_CID_mapping_certified=False);rows.append(summary);print('CONNECTION REPLAY PASS',case,arm,summary['successful'],summary['distinct_successful_native_pins'],summary['zero_success_pins'],flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as f:json.dump(dict(status='all6_native_connection_event_replays_and_per_iteration_counters_pass',bindings=bindings,rows=rows,scope='Complete observed native sink-pin domain inclzero events, explicit attempts/results, initial native tree reach flags and per-iteration native counter equality. Native-pin identities not yet authenticated as estimator manifest CIDs. Explicit sink re-invocations do not count shared-trunk side effects on other pins, or per-CID heap/time. No new policy, native runtime benefit, failure classifier, independent-family or original-zero-counter gate promotion.'),f,indent=2)
 print('ALL6CONNECTION REPLAYS PASS',flush=True)
if __name__=='__main__':main()
