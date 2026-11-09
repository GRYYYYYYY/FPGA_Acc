"""Read-only replay of per-net native quality decisions; no router imports."""
import collections,csv,hashlib,json,struct,xml.etree.ElementTree as ET
from decimal import Decimal
from native_STA_task_binding_v2 import make_binder
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_refreshed_critical_policy_v1_20261016'
def main():
 refs={}
 def sha(path):
  path=Path(path);h=hashlib.sha256()
  with path.open('rb') as stream:
   for block in iter(lambda:stream.read(1048576),b''):h.update(block)
  refs[str(path)]=h.hexdigest();return h.hexdigest()
 def load(path):sha(path);return json.loads(Path(path).read_text())
 def rows(path):sha(path);return list(csv.DictReader(Path(path).open()))
 def tree(path):
  result={};sources={}
  for row in rows(path):
   net=int(row['net_id']);v=int(row['child']);u=int(row['parent']);source=int(row['source'])
   assert net not in sources or sources[net]==source;sources[net]=source
   assert v not in result.setdefault(net,{}) or result[net][v]==u
   result[net][v]=u
  return result,sources
 protocol=load(P/'protocol.json');terminal=load(P/'manifest.json')
 assert terminal['status']=='three_case_single_sweeps_complete_requires_independent_review'
 for document in [protocol]:
  for path,h in document['source_sha256'].items():assert sha(path)==h,path
 outcomes=[]
 for case in protocol['cases']:
  label=case['label'];D=P/label;state=load(D/'manifest.json');assert state['status']=='single_sweep_complete_requires_independent_review'
  tasks={int(v['id']):v for v in rows(case['connections'])};by_net=collections.defaultdict(list)
  for task,row in tasks.items():by_net[int(row['net_id'])].append(task)
  lengths={}
  for _,e in ET.iterparse(Path(case['native_case'])/'rr_graph.xml',events=('end',)):
   if e.tag=='node':
    a=e.attrib;l=e.find('loc');value=0
    if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':value=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
    lengths[int(a['id'])]=value;e.clear()
   elif e.tag=='edge':e.clear()
  die=[v[0] for v in struct.iter_unpack('<H',Path(case['topology_prefix']+'.node_die').read_bytes())]
  def wire(t):return sum(lengths[v] for parent in t.values() for v in parent)
  def cross(t):return sum(die[v]!=die[u] for parent in t.values() for v,u in parent.items())
  def observation(directory):
   inputs=rows(directory/'observation.input.csv');outputs=rows(directory/'observation.output.csv')
   assert len(inputs)==len(outputs)==len(tasks)
   for v in inputs:
    task=int(v['task_id']);assert int(v['routed'])==int(v['delay_ps'])==0
    assert tuple(int(v[k]) for k in ['net_id','source','sink'])==tuple(int(tasks[task][k]) for k in ['net_id','source','sink'])
   result={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in outputs};assert set(result)==set(tasks)
   return result
  current,sources=tree(D/'initial/route.route_trees.csv');assert set(current)==set(by_net)
  frozen=Path(case['policy_parent_tree']).parent;original,_=tree(frozen/'route.route_trees.csv');assert current==original
  quality=load(D/'initial/native_validation/validation.json');frozen_quality=load(frozen/'native_validation/validation.json')
  assert quality['legal'] and quality['total_wirelength']==wire(current)
  assert (quality['total_wirelength'],quality['critical_path_delay_ns'])==(frozen_quality['total_wirelength'],frozen_quality['critical_path_delay_ns'])
  observed=observation(D/'initial');baseline,_=tree(case['native_tree']);baseline_cross=cross(baseline)
  assert baseline_cross==state['baseline_crossings']
  binder=make_binder(case['native_case'],case['connections']);attempted=set();epoch=0
  current_tree=D/'initial/route.route_trees.csv';accepted=0;native_calls=1
  for rank,step in enumerate(state['steps']):
   net=step['net'];assert step['rank']==rank and step['epoch']==epoch
   bound=binder(current_tree.parent/'native_validation/report_timing.setup.rpt',case['baseline_cpd_ns'])
   candidates=[]
   endpoint_delay={p['endpoint']:Decimal(p['effective_delay_ns']) for p in bound['paths']}
   for arc in bound['arcs']:
    if arc['intracluster']:continue
    t=int(arc['task']['id']);n=int(arc['task']['net_id'])
    if n not in attempted:candidates.append((-endpoint_delay[arc['endpoint']],-observed[t]['delay_ps'],t,n,arc['endpoint']))
   selected=min(candidates);critical_task=selected[2]
   assert (net,step['critical_task'],step['selected_endpoint'])==(selected[3],critical_task,selected[4])
   attempted.add(net)
   limit=Decimal(str(case['baseline_cpd_ns']));limit_ps=int(limit*1000)
   other_cross=cross({n:p for n,p in current.items() if n!=net})
   assert step['net_crossing_budget']==baseline_cross-other_cross>=0
   expected_order=sorted(by_net[net],key=lambda t:(t!=critical_task,-observed[t]['criticality_q'],t))
   assert [v['task'] for v in step['searches']]==expected_order[:len(step['searches'])]
   for search in step['searches']:
    task=search['task'];cap=max(0,observed[task]['delay_ps']+limit_ps+observed[task]['slack_ps'])
    assert 0<=search['before_crossings']<=step['net_crossing_budget']
    assert search['delay_cap_ps']==cap and search['labels']<=2097152 and search['expanded']<=search['labels']
   expected_accept=False
   if 'native_evidence' in step:
    native_calls+=1;directory=Path(step['native_evidence']);candidate,candidate_sources=tree(directory/'route.route_trees.csv')
    assert set(candidate)==set(current) and candidate_sources==sources
    assert {n for n in current if candidate[n]!=current[n]}<={net}
    assert cross(candidate)==step['candidate_crossings']<=baseline_cross
    assert cross({net:candidate[net]})<=step['net_crossing_budget']
    checked=step['validation']
    if checked['valid']:
     q=load(directory/'native_validation/validation.json');assert q==checked['quality'] and q['legal']
     assert q['inputs']['vpr_sha256']==protocol['source_sha256'][protocol['vpr']]
     assert sha(directory/'native.route')==q['inputs']['route_sha256']
     assert q['total_wirelength']==wire(candidate)
     expected_accept=(q['total_wirelength']<=max(quality['total_wirelength'],case['baseline_wirelength']) and q['critical_path_delay_ns']<quality['critical_path_delay_ns'])
     if expected_accept:
      current=candidate;quality=q;observed=observation(directory);current_tree=directory/'route.route_trees.csv';accepted+=1;epoch+=1;attempted=set()
   assert step['accepted']==expected_accept,(label,rank)
  assert accepted==state['accepted'] and state['current_quality']==quality
  assert Path(state['current_tree'])==current_tree and state['final_crossings']==cross(current)
  # Reconstruct every final connection, capacities and original graph edges.
  nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()));resources=list(struct.iter_unpack('<HHHHII',Path(case['input_prefix']+'.resources').read_bytes()));occupancy=collections.Counter()
  for net,parent in current.items():
   occupancy.update(parent.keys())
   for task in by_net[net]:
    source=int(tasks[task]['source']);v=int(tasks[task]['sink']);visited=set()
    while v!=source:
     assert v in parent and v not in visited;visited.add(v);u=parent[v];start,count,_=nodes[u];assert any(dst==v for dst,_,w in edges[start:start+count]);v=u
    assert len(visited)<=int(tasks[task]['max_hops'])
  assert all(n<=resources[v][1] for v,n in occupancy.items())
  outcomes.append(dict(case=label,net_attempts=len(state['steps']),accepted=accepted,native_calls=native_calls,wirelength=quality['total_wirelength'],cpd_ns=quality['critical_path_delay_ns'],crossings=cross(current),joint_baseline_pass=quality['total_wirelength']<=case['baseline_wirelength'] and quality['critical_path_delay_ns']<=case['baseline_cpd_ns'] and cross(current)<=baseline_cross))
 sha(Path(__file__).resolve());report=dict(status='three_refreshed_policy_cases_selection_budgets_native_decisions_and_final_connectivity_replayed',outcomes=outcomes,source_sha256=refs,adopted=False,research_complete=False,scope='CPU incremental postprocessing from audited v2 final states; shared packed-wiring binder replay, independent selection/budget/acceptance arithmetic and final graph/tree/capacity checks; not an independent optimal search proof. Not hardware publication/versions, repeats, heldout or physical performance.')
 with (P/'independent_audit.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=outcomes)))
if __name__=='__main__':main()
