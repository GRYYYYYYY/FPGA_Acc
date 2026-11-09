"""Bind every diagnostic search record to independently audited complete model queries."""
import json,sys,math
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=Path(sys.argv[1]).resolve();rp=D/'receipt.json';r=json.loads(rp.read_text());bindings={**closure([Path(__file__)]),str(rp):sha(rp)}
for section in ['bindings','files']:
 for p,h in r[section].items():assert sha(p)==h
for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
 p=D/name;a=json.loads(p.read_text());assert a['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(f)==h for f,h in a['bindings'].items());bindings[str(p)]=sha(p)
assert a['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
epfile=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'));ep=json.loads(epfile.read_text());groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
f=D/'search_work.json';assert sha(f)==r['files'][str(f)];work=json.loads(f.read_text());bindings[str(f)]=sha(f);bindings[str(epfile)]=sha(epfile)
phases=[('initial',sorted(groups))]+[(f'feedback_{row["round_index"]}',row['affected_nets']) for row in r['rounds']];assert work['initial_queries']==len(groups);assert work['round_queries']==[len(row['affected_nets']) for row in r['rounds']];metrics=work['metrics'];assert len(metrics)==sum(len(nets) for phase,nets in phases);index=0;summary={}
for phase,nets in phases:
 for net in nets:
  m=metrics[index];index+=1;qs=groups[net];sources={q['source'] for q in qs};targets=len({q['sink'] for q in qs});assert len(sources)==1 and m['source']==next(iter(sources)) and m['targets']==targets
  kind='singleton_bidirectional' if targets==1 else 'multitarget_forward';assert m['branch']==kind;assert math.isfinite(m['seconds']) and m['seconds']>=0;counts=m['counts'];assert m['counts_available']==(counts is not None)
  row=summary.setdefault(phase+':'+kind,dict(queries=0,seconds=0.0,counts_missing=0,reported_scanned_arcs=0,reported_settled_nodes=0));row['queries']+=1;row['seconds']+=m['seconds']
  if counts is None:assert kind=='singleton_bidirectional';row['counts_missing']+=1;continue
  if kind=='singleton_bidirectional':
   arcs=counts['scanned_arcs_by_direction'];settled=counts['settled_nodes_by_direction'];assert len(arcs)==len(settled)==2
  else:
   assert counts['source']==m['source'] and counts['targets']==targets;assert counts['pushes']==counts['relaxations']+1 and counts['stale']<=counts['pops']<=counts['pushes'];assert counts['settled']<=counts['touched'];arcs=[counts['scanned_arcs']];settled=[counts['settled']]
  assert all(type(x) is int and x>=0 for x in arcs+settled);row['reported_scanned_arcs']+=sum(arcs);row['reported_settled_nodes']+=sum(settled)
assert sum(row['seconds'] for row in summary.values())<=r['cpp_search_seconds'];assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,all_search_records_match_full_original_NET_phase_and_dispatch=True,search_records=index,summary=summary,scope='Diagnostic per-branch instrumented timings and kernel-reported work, linked to full independent model audits. Missing bidi counters explicit; totals are reported available work, not inferred zero or independent kernel-counter reconstruction. No complete workflow speedup, heldout or native QoR claim.')
(D/'branch_work_verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(summary,indent=2))
