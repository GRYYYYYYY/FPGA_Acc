"""Independent token replay of old/cold native NET unions and group error sums."""
import array,collections,json,sys
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_cold_route_turnover_v1_2026-10-18';rp=root/'results.json';r=json.loads(rp.read_text());assert all(sha(k)==h for k,h in r['bindings'].items());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};idx=json.loads((E/'real_joint_full_score_v2_2026-10-18/graph_index.json').read_text());dest=array.array('I');dest.frombytes(Path(idx['arrays']['edge_destination']['path']).read_bytes());oldgeo=json.loads((E/'mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());oldroute=Path(oldgeo['previous_native_route']);assert sha(oldroute)==oldgeo['bindings'][str(oldroute)];bindings[str(oldroute)]=sha(oldroute);bindings[str(E/'mmc_native_state_geometry_v1_2026-10-18/protocol.json')]=sha(E/'mmc_native_state_geometry_v1_2026-10-18/protocol.json');oldframe=json.loads((E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json').read_text());rows=[]
 def parse(path,lookup):
  sets={};current=None
  with path.open() as f:
   for line in f:
    s=line.strip()
    if s.startswith('Net '):
     left,rest=s.split('(',1);name,suffix=rest.rsplit(')',1);current=lookup.get(name) if not suffix.strip() else None;continue
    words=s.split()
    if words and words[0]=='Node:':
     assert current is not None and len(words)>2;node=int(words[1]);sets.setdefault(current,set()).add(node)
  assert set(sets)==set(lookup.values());return sets
 def projected(frame,domain):
  ret=collections.defaultdict(set)
  for rec in frame['records']:
   target=ret[rec['net_id']]
   if rec['source'] in domain:target.add(rec['source'])
   target.update(dest[e] for e in rec['answer']['physical_edge_ids'] if dest[e] in domain)
  return ret
 for case in ['case_01','case_02','case_03']:
  qp=E/f'mmc_owner_expansion_quality_v1_2026-10-18/{case}';q=json.loads((qp/'protocol.json').read_text());ep=json.loads(Path(q['endpoint']).read_text());vectors=json.loads((qp/'vectors.json').read_text());caps={c['node']:c['capacity'] for c in vectors['channels']};domain=set(caps);ids={rec['net_id'] for rec in oldframe['records']};lookup={ep['net_names'][str(n)]:n for n in ids};old_all=parse(oldroute,lookup);cold_all=parse(Path(q['native_admission']).parent/'cold/output.route',lookup);old={n:v&domain for n,v in old_all.items()};cold={n:v&domain for n,v in cold_all.items()};assert projected(oldframe,domain)==old
  model=E/f'mmc_owner_expansion_feedback_v1_2026-10-18/{case}';frame=json.loads((model/'sketch.json').read_text());pred=projected(frame,domain);warm=json.loads((Path(q['model_directory'])/'native_retained/verification.json').read_text());receipt=json.loads((model/'receipt.json').read_text());dirty=set(warm['dirty_nets']);scheduled={event['net_id'] for rr in receipt['rounds'] for event in rr['events']};groups={'endpoint_dirty':dirty,'added_owner':scheduled-dirty,'never_scheduled':ids-scheduled};stats=next(x for x in r['cases'] if x['case']==case);written=json.loads((root/case/'per_NET_turnover.json').read_text());assert len(written)==len(ids)==55300 and {x['net_id'] for x in written}==ids;table={x['net_id']:x for x in written};errs={}
  for group,members in groups.items():
   total=collections.Counter();changed=0;removed=0;added=0
   for net in members:
    a,b,c=old[net],pred[net],cold[net];row=dict(net_id=net,name=ep['net_names'][str(net)],group=group,old_channel_nodes=len(a),predicted_channel_nodes=len(b),cold_channel_nodes=len(c),cold_removed_from_old=len(a-c),cold_added_to_old=len(c-a),prediction_removed_from_old=len(a-b),prediction_added_to_old=len(b-a),prediction_cold_symmetric_difference=len(b^c));assert row==table[net];changed+=a!=c;removed+=len(a-c);added+=len(c-a);total.update(b);total.subtract(c)
    if group=='never_scheduled':assert a==b
   expected=stats['groups'][group];assert expected['NETs']==len(members) and expected['cold_changed_NETs']==changed and expected['cold_removed_NET_node_incidents']==removed and expected['cold_added_NET_node_incidents']==added;assert expected['old_channel_incidents']==sum(len(old[n]) for n in members) and expected['predicted_channel_incidents']==sum(len(pred[n]) for n in members) and expected['cold_channel_incidents']==sum(len(cold[n]) for n in members);errs[group]=total
  complete={n:sum(err[n] for err in errs.values()) for n in domain};assert all(complete[c['node']]==c['predictions']['owner_expansion_on']-c['labels']['cold'] for c in vectors['channels']);mae=sum((Fraction(abs(value),caps[n]) for n,value in complete.items()),Fraction(0))/len(domain);assert mae==Fraction(stats['channel_MAE_exact']);contributions=[]
  for group,err in errs.items():
   value=sum((Fraction(v*(1 if complete[n]>0 else -1 if complete[n]<0 else 0),caps[n]) for n,v in err.items() if n in domain),Fraction(0))/len(domain);l1=sum((Fraction(abs(v),caps[n]) for n,v in err.items() if n in domain),Fraction(0))/len(domain);expected=stats['groups'][group];assert value==Fraction(expected['channel_error_projection_exact']) and abs(float(l1)-expected['individual_group_L1_normalized'])<1e-14;assert abs(float(value/mae)-expected['share_of_total_channel_MAE'])<1e-14;contributions.append(value)
  assert sum(contributions,Fraction(0))==mae;rows.append(dict(case=case,NETs=len(ids),old_printed_route_to_frame_perNET_channel_unions_equal=True,cold_printed_route_perNET_turnover_exact=True,all3_group_channel_error_projection_sums_exact=True));print('TURNOVER INDEPENDENT PASS',case,flush=True)
 assert all(sha(k)==h for k,h in bindings.items())
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all3_independent_old_and_cold_native_token_union_and_exact_error_decompositions_pass',bindings=bindings,cases=rows,scope='Old route parsed independently by NET names and token node lexer, compared perNET with original source frame; cold token unions and all written NET turnover rows checked. Final model path projection uses previously originalXML-certified destination arrays and independently audited frames. Algebraic signed-error decomposition, not causal attribution or a rank impossibility theorem.'),f,indent=2)
if __name__=='__main__':main()
