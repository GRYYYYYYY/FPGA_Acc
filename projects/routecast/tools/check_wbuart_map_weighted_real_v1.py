"""Fixed NET0 real-graph primitive fixtures at matched warm owner-excluded prices."""
import json,hashlib,copy
from pathlib import Path
from fractions import Fraction as F
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from audit_structural_node_base_v1 import audit
from bound_native_map_query_v1 import Query,f32,frombits
from compiled_map_weighted_tree_v1 import Graph as New
from compiled_criticality_tree_v1 import Graph as Old
from check_map_weighted_retained_wide_v1 import reference
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_weighted_real_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);manifest=E/'wbuart_map_probe_targets_v1_2026-10-20/manifest.json';forecast=E/'wbuart_forecasts_v1_2026-10-20/verification.json';bindings={};rows=[]
 for case in read(manifest)['cases']:
  name=case['target_case'];ep=Path(case['endpoint']);graph,digest,nodes,fields,rc,queries=load_endpoints(ep);arm=Path(next(a['output'] for r in read(forecast)['rows'] if r['case']==name for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'));warm=read(arm/'initial.json');records=[q for q in warm['records'] if q['net_id']==0];slots={eid:i for i,eid in enumerate(fields['edge_ids'])};owned={q['source'] for q in records}|{fields['dest_ranks'][slots[e]] for q in records for e in q['answer']['physical_edge_ids']};ledger={int(n):x for n,x in warm['ledger'].items()};proof=E/'wbuart_node_bases_v1_2026-10-20'/name.split('/')[0]/'verification.json';base=audit(graph,proof,rc.scale);cost={}
  for n,node in enumerate(nodes):
   loc=node.find('loc');span=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1 if node.get('type') in ['CHANX','CHANY'] else 0
   cost[n]=base[n]*(1+max(0,ledger.get(n,0)-int(n in owned)-fields['capacities'][n]+1))+(rc.scale//20000000000)*span
  timing=E/'wbuart_frame_timings_v1_2026-10-20'/name/'initial_connection_criticalities.json';matrix=Path(case['output'])/'map_query.tsv';query=Query(matrix,ep,timing);cr={q['connection_id']:q for q in read(arm/'timing_round0.json')['criticalities']};pin={q['connection_id']:q['local_sink_pin'] for q in read(timing) if q['native_net_id']==0};inc=[rc.increment(i) for i in range(len(fields['dest_ranks']))];initial=[rc.initial(n) for n in range(len(nodes))];old,new,weighted=Old(fields,inc,initial),New(fields,inc,initial),New(fields,inc,initial);source=records[0]['source'];trees=[g.tree(source) for g in [old,new,weighted]];mask=[n in query.allowed for n in range(len(nodes))];cases=[]
  for rec in sorted(records,key=lambda r:(-F(cr[r['connection_id']]['criticality_numerator'],cr[r['connection_id']]['criticality_denominator']),r['connection_id'])):
   cid=rec['connection_id'];c=F(cr[cid]['criticality_numerator'],cr[cid]['criticality_denominator']);assert c==F.from_float(frombits(cr[cid]['criticality_bits']));H=[0]*len(nodes)
   for n in query.allowed:
    value=query.query(n,pin[cid],cr[cid]['criticality_bits'],graph_sha256=digest,endpoint_sha256=query.endpoint_sha256);v=F.from_float(f32(f32(1.2)*value))*rc.scale*c.denominator;H[n]=-(-v.numerator//v.denominator)
   target=rec['sink'];budget=rec['budget_integer'];a=trees[0].expand(target,c,cost,budget);b=trees[1].expand(target,c,cost,budget,[0]*len(nodes),mask);assert a==b and old.last_stats==new.last_stats and (trees[0].arrival,trees[0].parents)==(trees[1].arrival,trees[1].parents)
   before=copy.deepcopy((trees[2].arrival,trees[2].parents));expect,stats=reference(fields,inc,*before,source,target,c,cost,budget,H);w=trees[2].expand(target,c,cost,budget,H,mask);assert weighted.last_stats[:3]==stats
   for k,v in expect.items():assert w[k]==v
   if not w['committed']:assert (trees[2].arrival,trees[2].parents)==before
   for answer in [a,w]:
    if 'path_slots' not in answer:continue
    u=source;seen={u};raw=initial[u]
    for slot in answer['path_slots']:
     assert fields['row_offsets'][u]<=slot<fields['row_offsets'][u+1];u=fields['dest_ranks'][slot];assert u not in seen and mask[u];seen.add(u);raw+=inc[slot]
    assert u==target and raw==answer['raw'] and (raw<=budget)==answer['committed']
   cases.append({'CID':cid,'criticality':str(c),'budget':budget,'H0':a,'MAP':w,'H0_stats':list(old.last_stats),'MAP_stats':list(weighted.last_stats)})
  for g in [old,new,weighted]:g.close()
  rows.append({'case':name,'queries':cases});print(name,'PASS',flush=True)
  for p in [ep,graph,proof,matrix,timing,arm/'initial.json',arm/'timing_round0.json']:bindings[str(p)]=sha(p)
 for p in [Path(__file__),manifest,forecast,R/'tools/compiled_map_weighted_tree_v1.py',R/'tools/check_map_weighted_retained_wide_v1.py',R/'tools/bound_native_map_query_v1.py',R/'build/map_weighted_criticality_v1_2026-10-20/search.so']:bindings[str(p)]=sha(p)
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_REAL_GRAPHS_NET0_18_RETAINED_QUERIES_H0_PARITY_AND_MAP_REFERENCE_PASS','rows':rows,'bindings':bindings,'scope':'Fixed warm owner-excluded snapshot, source-start two-target retained tree only. No whole NET acceptance, full sketch/native numeric equivalence, quality or paid gain proof.'},indent=2)+'\n')
if __name__=='__main__':main()
