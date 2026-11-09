"""Existing exposed cold-route turnover; labels never choose model scheduling."""
import array,collections,json,re,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from audit_native_route import NODE
HEADER=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(.*)$')

def main():
 E=R/'experiments';out=E/'mmc_cold_route_turnover_v1_2026-10-18';out.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);rows=[]
 def load(p):p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  d=load(p);assert all(sha(k)==h for k,h in d['bindings'].items());bindings.update(d['bindings']);return d
 decision=admit(E/'mmc_owner_expansion_feedback_v1_2026-10-18/research_decision_v1.json');assert not decision['all3_original_cold_gate_pass'];geo=admit(E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json');geoproof=admit(E/'mmc_endpoint_geometry_topology_v2_2026-10-18/independent_verification_v1.json');idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';assert geo['bindings'][str(idxp)]==sha(idxp);idx=load(idxp);arrays={}
 for key in ['edge_source','edge_destination']:
  d=idx['arrays'][key];assert sha(d['path'])==d['sha256']==geo['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());assert len(a)==d['values'] and sys.byteorder==idx['byteorder'];arrays[key]=a;bindings[d['path']]=d['sha256']
 oldp=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';oldproof=admit(oldp.parent/'independent_xml_verification_v1.json');assert oldproof['all_native_paths_exact'] and oldproof['bindings'][str(oldp)]==sha(oldp);old=load(oldp)
 def owners(frame):
  nets=collections.defaultdict(set)
  for rec in frame['records']:
   u=rec['source'];seen={u}
   for edge in rec['answer']['physical_edge_ids']:
    assert arrays['edge_source'][edge]==u;u=arrays['edge_destination'][edge];assert u not in seen;seen.add(u)
   assert u==rec['sink'];nets[rec['net_id']].update(seen)
  assert dict(collections.Counter(n for ns in nets.values() for n in ns))=={int(n):v for n,v in frame['ledger'].items()};return dict(nets)
 oldowners=owners(old)
 protocol=dict(scope='All3 already exposed cases; descriptive cold-route changes by endpoint-dirty, added actually scheduled owners, and never-scheduled NETs. No new model or label-based selection.',partition='Dirty from existing warm proof; added owners = union of both actual affected_NET sets minus dirty; untouched = all remaining NETs. Compare previous native and final candidate to accepted cold perNET unions.',metrics='PerNET channel-set turnover and occupancy errors. Signed projection onto total error gives an exact additive group decomposition of channel MAE; individual group L1 errors can cancel and must not be summed as total MAE. Neither algebraic contribution nor label-based turnover is a causal proof, ranking impossibility bound or deployable feature.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
 for case in ['case_01','case_02','case_03']:
  qroot=E/f'mmc_owner_expansion_quality_v1_2026-10-18/{case}';qproof=admit(qroot/'verification.json');assert qproof['status']=='pass';qp=load(qroot/'protocol.json');vectors=load(qroot/'vectors.json');channels={r['node']:r for r in vectors['channels']};domain=set(channels);ep=load(qp['endpoint']);names={int(n):name for n,name in ep['net_names'].items() if int(n) in oldowners};assert len(names)==len(set(names.values()))==55300;assert set(names)=={q['net_id'] for q in ep['connections']}==set(oldowners);byname={name:n for n,name in names.items()}
  native=admit(qp['native_admission']);assert native['all_native_physical_and_canonical_pass'];route=Path(qp['native_admission']).parent/'cold/output.route';bindings[str(route)]=sha(route);assert bindings[str(route)]==native['bindings'][str(route)];cold=collections.defaultdict(set);current=None
  with route.open() as stream:
   for line in stream:
    h=HEADER.match(line)
    if h:current=byname.get(h[2]) if not h[3].strip() else None;continue
    m=NODE.match(line)
    if m:assert current is not None;cold[current].add(int(m[1]))
    elif line.lstrip().startswith('Node:'):raise ValueError('unparsed node')
  assert set(cold)==set(names);actual=collections.Counter(n for ns in cold.values() for n in ns);physical=load(qp['labels']['cold']);assert dict(actual)=={int(n):v for n,v in physical['node_occupancy'].items()}
  model=E/f'mmc_owner_expansion_feedback_v1_2026-10-18/{case}';receipt=admit(model/'receipt.json');frame=load(model/'sketch.json');assert receipt['files'][str(model/'sketch.json')]==sha(model/'sketch.json');pred=owners(frame);warm=admit(Path(qp['model_directory'])/'native_retained/verification.json');dirty=set(warm['dirty_nets']);scheduled=set().union(*(set(rr['affected_nets']) for rr in receipt['rounds']));assert dirty<=scheduled;groups={'endpoint_dirty':dirty,'added_owner':scheduled-dirty,'never_scheduled':set(names)-scheduled};assert sum(map(len,groups.values()))==55300
  for net in groups['never_scheduled']:assert pred[net]==oldowners[net]
  folder=out/case;folder.mkdir();netrows=[];errors={};groupstats={}
  for name,nets in groups.items():
   oldcount=collections.Counter();newcount=collections.Counter();coldcount=collections.Counter();changed=0;removed=0;added=0
   for net in sorted(nets):
    a=oldowners[net]&domain;b=pred[net]&domain;c=cold[net]&domain;oldcount.update(a);newcount.update(b);coldcount.update(c);removed+=len(a-c);added+=len(c-a);changed+=a!=c;netrows.append(dict(net_id=net,name=names[net],group=name,old_channel_nodes=len(a),predicted_channel_nodes=len(b),cold_channel_nodes=len(c),cold_removed_from_old=len(a-c),cold_added_to_old=len(c-a),prediction_removed_from_old=len(a-b),prediction_added_to_old=len(b-a),prediction_cold_symmetric_difference=len(b^c)))
   error=newcount.copy();error.subtract(coldcount);errors[name]=error;groupstats[name]=dict(NETs=len(nets),cold_changed_NETs=changed,cold_removed_NET_node_incidents=removed,cold_added_NET_node_incidents=added,old_channel_incidents=sum(oldcount.values()),predicted_channel_incidents=sum(newcount.values()),cold_channel_incidents=sum(coldcount.values()))
  total=collections.Counter()
  for err in errors.values():total.update(err)
  hist=collections.Counter()
  for node,cell in channels.items():
   assert actual[node]==cell['labels']['cold'];expected=cell['predictions']['owner_expansion_on']-cell['labels']['cold'];assert total[node]==expected;hist[cell['capacity']]+=abs(expected)
  mae=sum((F(v,c) for c,v in hist.items()),F(0))/len(domain);contributions={}
  for name,error in errors.items():
   signed=collections.Counter();absolute=collections.Counter()
   for node,cell in channels.items():signed[cell['capacity']]+=(1 if total[node]>0 else -1 if total[node]<0 else 0)*error[node];absolute[cell['capacity']]+=abs(error[node])
   value=sum((F(v,c) for c,v in signed.items()),F(0))/len(domain);l1=sum((F(v,c) for c,v in absolute.items()),F(0))/len(domain);contributions[name]=value;groupstats[name].update(channel_error_projection_exact=str(value),channel_error_projection=float(value),share_of_total_channel_MAE=float(value/mae) if mae else None,individual_group_L1_normalized=float(l1))
  assert sum(contributions.values(),F(0))==mae;np=folder/'per_NET_turnover.json';np.write_text(json.dumps(sorted(netrows,key=lambda r:r['net_id'])));bindings[str(np)]=sha(np);rows.append(dict(case=case,channel_MAE_exact=str(mae),channel_MAE=float(mae),groups=groupstats));print('TURNOVER',case,json.dumps(groupstats),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(out/'results.json').write_text(json.dumps(dict(status='all3_perNET_cold_turnover_and_exact_channel_error_projection_computed_independent_verification_pending',bindings=bindings,cases=rows,scope=protocol),indent=2))
if __name__=='__main__':main()
