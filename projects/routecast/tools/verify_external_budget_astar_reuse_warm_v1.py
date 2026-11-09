"""Independent original Expat/Fraction zero-RC full forecast audit, overload allowed."""
import json,sys,xml.parsers.expat
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_budget_astar_reuse_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='ALL3_BUDGET_ASTAR_REUSE_WARM_FRAMES_AND_RAW_BOUND_CERTIFICATES_PREPARED'
 for x in [proof,protocol]:assert all(sha(p)==h for p,h in x['bindings'].items())
 boundproof_path=D/'remaining_bounds_independent_verification_v1.json';boundproof=read(boundproof_path);assert boundproof['status']=='ALL_EXPORTED_RELAXED_RAW_BOUNDS_ORIGINAL_XML_BELLMAN_CERTIFIED';assert all(sha(p)==h for p,h in boundproof['bindings'].items());bound_meta=read(D/'remaining_delay_bounds/manifest.json');bound_keys={(r['target'],r['cap']) for r in bound_meta['bounds']};bound_seen=set();bound_hits=0
 graph=Path(read(protocol['cases'][0]['endpoint'])['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);caps.append(int(attrs['capacity']));types.append(attrs['type'])
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);value=Fraction(attrs.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;weights[active['switch']]=value.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));switches.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert timings==len(caps);digest=sha(graph);bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json',graph,boundproof_path,D/'remaining_delay_bounds/manifest.json']};rows=[]
 for spec in protocol['cases']:
  case=spec['case'];fp=D/case/'frame.json';frame=read(fp);base=read(spec['base_frame']);ep=read(spec['endpoint']);assert frame['scale']==base['scale']==10**18 and frame['graph_sha256']==base['graph_sha256']==ep['graph_sha256']==digest;assert sha(ep['inputs']['graph']['path'])==digest;qs={q['connection_id']:q for q in ep['connections']};old={r['connection_id']:r for r in base['records']};new={r['connection_id']:r for r in frame['records']};assert len(new)==len(frame['records'])==len(qs)==15616 and set(new)==set(old)==set(qs);state_rows=list(map(json.loads,Path(spec['partial_state']).read_text().splitlines()));state={r['net_id']:r['candidate'] for r in state_rows};groups=defaultdict(set)
  for cid,r in old.items():groups[r['net_id']].add(cid)
  assert len(state)==len(state_rows)
  for net,c in state.items():
   incoming={r['connection_id']:r for r in c['records']};assert len(incoming)==len(c['records']) and set(incoming)==groups[net]
   for cid,r in incoming.items():assert new[cid]==r
  unions=defaultdict(set);independent=Counter();parents=defaultdict(dict);changed=set()
  for cid,r in new.items():
   q=qs[cid];assert (r['net_id'],r['source'],r['sink'])==(q['net_id'],q['source'],q['sink']);assert {k:v for k,v in r.items() if k!='answer'}=={k:v for k,v in old[cid].items() if k!='answer'}
   if r['net_id'] not in state:assert r==old[cid]
   if r!=old[cid]:changed.add(r['net_id'])
   u=r['source'];assert types[u]=='SOURCE' and caps[u]>0;seen={u};value=0;edges=r['answer']['physical_edge_ids'];assert r['answer']['status']=='FOUND' and edges
   for pos,eid in enumerate(edges):
    assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and caps[v]>0
    if pos<len(edges)-1:assert types[v] not in ['SOURCE','SINK']
    if types[v]!='SINK':assert v not in parents[r['net_id']] or parents[r['net_id']][v]==(u,eid);parents[r['net_id']][v]=(u,eid)
    seen.add(v);value+=weights[switches[eid]];u=v
   assert u==r['sink'] and types[u]=='SINK' and value==r['answer']['delay']<=r['budget_integer'];assert type(r['budget_integer']) is int;unions[r['net_id']].update(seen);independent.update(seen)
  ledger=Counter(node for ns in unions.values() for node in ns);assert len(unions)==5919;assert {int(n):v for n,v in frame['ledger'].items()}==dict(ledger);assert {int(n):v for n,v in frame['independent_connection_ledger'].items()}==dict(independent);overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());assert frame['overflow_units']==overflow and frame['overflow_nodes']==sum(v>caps[n] for n,v in ledger.items());assert frame['eligible_for_legal_route_commit'] is False and frame['history']=={};assert frame['budget_policy']==base['budget_policy'];assert frame['epochs']=={str(n):v+int(int(n) in changed) for n,v in base['epochs'].items()};assert frame['required_connections']==frame['completed_connections']==len(new);row=dict(case=case,all_CIDs=len(new),NETs=len(unions),changed_NETs=len(changed),fullgraph_overflow=overflow,base_overflow=base['overflow_units'],all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True);rows.append(row)
  native_path=Path(spec['source_frame']);native={r['connection_id']:r for r in read(native_path)['records']};events_path=D/case/'events.json';events=read(events_path);assert [e['net_id'] for e in events]==sorted(spec['dirty_NETs']);penalty=len(caps)*max(weights[s] for s in switches)+1;fallbacks=0
  for e in events:
   net=e['net_id'];cids=groups[net];eligible=sorted(cid for cid in cids if (new[cid]['source'],new[cid]['sink'])==(native[cid]['source'],native[cid]['sink']));ns={native[cid]['source'] for cid in cids}
   for cid in cids:ns.update(vs[edge] for edge in native[cid]['answer']['physical_edge_ids'])
   assert e['label_limit']==10000 and len(e['repair_searches'])==e['repair_calls']
   for query in e['repair_searches']:
    key=(query['bound_target'],query['bound_cap']);assert key==(new[query['CID']]['sink'],new[query['CID']]['budget_integer']+1) and key in bound_keys;assert query['bound_context_sha256']==bound_meta['context_sha256'];assert query['bound_cache_hit']==(key in bound_seen);bound_hits+=int(key in bound_seen);bound_seen.add(key)
    assert query['label_limit']==10000 and 0<=query['expanded']<=query['labels_created']<=10000
    if query['status']=='COMMITTED':assert query['raw']<=new[query['CID']]['budget_integer']
    else:assert e['whole_NET_fallback'] and e['fallback_reason']==query['status']
   assert e['novelty_penalty_integer']==penalty and e['native_CHANNEL_nodes']==sum(types[n] in ['CHANX','CHANY'] for n in ns);assert e['attempted_retained_connection_ids']==eligible;assert e['changed_CIDs']==sorted(cid for cid in cids if new[cid]['answer']!=old[cid]['answer'])
   if e['whole_NET_fallback']:
    fallbacks+=1;assert e['fallback_reason'] is not None and e['retained_connection_ids']==[];assert all(new[cid]==old[cid] for cid in cids)
   else:
    assert e['fallback_reason'] is None and e['retained_connection_ids']==eligible;assert e['repair_calls']==len(cids)-len(eligible)
   for cid in eligible:assert new[cid]['answer']['physical_edge_ids']==native[cid]['answer']['physical_edge_ids']
  for cid,r in new.items():
   if (r['source'],r['sink'])==(native[cid]['source'],native[cid]['sink']):assert r['answer']['physical_edge_ids']==native[cid]['answer']['physical_edge_ids']
  row['initializer_event_semantics_independently_verified']=True;row['whole_NET_fallbacks_verified']=fallbacks
  for p in [native_path,events_path,fp,Path(spec['base_frame']),Path(spec['partial_state']),Path(spec['endpoint'])]:bindings[str(p)]=sha(p)
  print('FULL_FORECAST_OVERLAY_INDEPENDENT_PASS',json.dumps(row),flush=True)
 assert bound_seen==bound_keys and bound_hits==bound_meta['cache_hits'] and len(bound_seen)==bound_meta['cache_misses'];assert all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL3_BUDGET_ASTAR_REUSE_WARM_ORIGINAL_XML_FRACTION_BUDGETS_LEDGERS_AND_BOUND_EVENTS_VERIFIED',rows=rows,all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,bindings=bindings,scope='All complete frame paths and counters verified; overload is explicitly allowed in forecast, not legally routed or objective-guarded native candidate. Reset history is no feedback continuation. Existing exposed development inputs only, no quality/utility or full-time success.'),indent=2)+'\n')
if __name__=='__main__':main()
