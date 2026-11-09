"""Derive one warm-update engine with explicit all/local scheduling and auditor."""
import ast,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
p=R/'tools/run_explicit_epoch_cached_retained_tree_v1.py';s=p.read_text()
s=s.replace('criticality_directory,retain_context=False):','criticality_directory,warm_directory,scheduling,retain_context=False):',1)
marker=' criticality_graph=CriticalityGraph';i=s.index(marker)
s=s[:i]+''' warm_directory=Path(warm_directory).resolve();warm_proof=warm_directory/'verification.json';warm=json.loads(warm_proof.read_text())
 assert scheduling in ['all','local'] and Path(warm['endpoint']).resolve()==endpoint
 assert warm['old_unaffected_records_exactly_preserved'] and warm['dirty_records_equal_independent_full_initial'] and warm['epochs_carried_and_dirty_bumped'] and warm['history_exactly_previous_round1']
 assert all(sha(p)==h for p,h in warm['bindings'].items());bindings.update(warm['bindings']);bindings[str(warm_proof)]=sha(warm_proof)
 dirty=set(warm['dirty_nets']);assert dirty<=set(groups)
'''+s[i:]
s=s.replace("scheduling_policy='all_NETs_each_round',", "scheduling_policy='all_NETs_each_round' if scheduling=='all' else 'endpoint_closure_NETs_each_round',warm_seed_proof=str(warm_proof),")
s=s.replace('initial history addition skipped; old owner excluded','initial history inherited from prior round1; addition skipped at update round0; old owner excluded')
s=s.replace('Complete two-round criticality feedback: original zero-price initial floors/budgets;','Warm two-round placement update: unchanged routes preserved, moved-closure floors recomputed; inherited epochs/history;')
a=s.index(' for net,qs in sorted(groups.items()):');b=s.index(' seed=candidate;',a)
s=s[:a]+''' candidate=json.loads((warm_directory/'initial.json').read_text());assert candidate['completed_connections']==candidate['required_connections']==len(queries)
 floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((warm_directory/'floors.json').read_text())}
 independent=Counter({int(n):v for n,v in candidate['independent_connection_ledger'].items()})
'''+s[b:]
s=s.replace("prices=Counter(span_prices);epochs={n:1 for n in groups}","prices=Counter({int(n):v for n,v in json.loads((warm_directory/'history.json').read_text()).items()});epochs={int(n):v for n,v in seed['epochs'].items()}")
s=s.replace('affected=sorted(groups);events=[]','affected=sorted(groups if scheduling=="all" else dirty);events=[]')
s=s.replace("['endpoint','output','node_base_proof','criticality_directory']","['endpoint','output','node_base_proof','criticality_directory','warm_directory','scheduling']")
s=s.replace('args.node_base_proof,args.criticality_directory)','args.node_base_proof,args.criticality_directory,args.warm_directory,args.scheduling)')
s=s.replace("candidate=dict(seed,records=final['records'],ledger=final['ledger']","candidate=dict(seed,records=final['records'],epochs=final['epochs'],ledger=final['ledger']")
ast.parse(s);(R/'tools/run_warm_epoch_retained_update_v1.py').write_text(s)
p=R/'tools/verify_explicit_epoch_retained_full_schedule_v1.py';s=p.read_text()
old="assert p['price_unit_integer']==scale//(20*10**9);epochs={n:1 for n in records};prices=Counter()"
assert old in s
new='''assert p['price_unit_integer']==scale//(20*10**9)
wp=Path(p['warm_seed_proof']);warm=json.loads(wp.read_text());assert all(sha(q)==h for q,h in warm['bindings'].items());bindings.update(warm['bindings']);bindings[str(wp)]=sha(wp)
assert seed==json.loads((wp.parent/'initial.json').read_text())
previous=Path(warm['previous_model']);prior=json.loads((previous/'round1.json').read_text());before=json.loads(Path(json.loads((Path(p['criticality_input_proof'])).read_text())['before_endpoint']).read_text())
a={q['connection_id']:q for q in before['connections']};b={q['connection_id']:q for q in ep['connections']};assert set(a)==set(b)
dirty=set();sources=set()
for cid in a:
 if a[cid]!=b[cid]:
  for q in [a[cid],b[cid]]:dirty.add(q['net_id']);sources.add(q['source'])
while True:
 prev=(len(dirty),len(sources))
 for q in list(a.values())+list(b.values()):
  if q['net_id'] in dirty or q['source'] in sources:dirty.add(q['net_id']);sources.add(q['source'])
 if prev==(len(dirty),len(sources)):break
assert sorted(dirty)==warm['dirty_nets']
old_records={q['connection_id']:q for q in json.loads((previous/'sketch.json').read_text())['records']}
for rec in seed['records']:
 if rec['net_id'] not in dirty:assert rec==old_records[rec['connection_id']]
epochs={int(n):e+int(int(n) in dirty) for n,e in prior['epochs'].items()};assert epochs=={int(n):e for n,e in seed['epochs'].items()}
prices=Counter({int(n):v for n,v in prior['prices'].items()});assert dict(prices)=={int(n):v for n,v in json.loads((wp.parent/'history.json').read_text()).items()}
assert p['scheduling_policy'] in ['all_NETs_each_round','endpoint_closure_NETs_each_round']'''
s=s.replace(old,new)
s=s.replace('prices.update(span_prices);checked=','assert all(prices[n]>=v for n,v in span_prices.items());checked=')
s=s.replace('initial history addition skipped; old owner excluded','initial history inherited from prior round1; addition skipped at update round0; old owner excluded')
s=s.replace('affected=sorted(records);assert affected==','affected=sorted(records if p["scheduling_policy"]=="all_NETs_each_round" else dirty);assert affected==')
s=s.replace("assert c['records']==state['records'] and c['ledger']==state['ledger']","assert c['epochs']==state['epochs'] and c['records']==state['records'] and c['ledger']==state['ledger']")
ast.parse(s);(R/'tools/verify_warm_epoch_retained_update_v1.py').write_text(s)
print('Warm update model and independent inherited-state/scheduling auditor prepared')
