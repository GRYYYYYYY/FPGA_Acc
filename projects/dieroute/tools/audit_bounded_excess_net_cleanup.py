"""Read-only replay of per-net native quality decisions; no router imports."""
import collections,csv,hashlib,json,struct,sys,xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=Path(sys.argv[1]).resolve()
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
 assert terminal['status']=='bounded_excess_net_cleanup_terminal_requires_review'
 for document in [protocol,load(P/'launch_protocol.json')]:
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
  frozen=Path(case['repeat_parent_directory']);original,_=tree(frozen/'route.route_trees.csv');assert current==original
  quality=load(D/'initial/native_validation/validation.json');frozen_quality=load(frozen/'native_validation/validation.json')
  assert quality['legal'] and quality['total_wirelength']==wire(current)
  assert (quality['total_wirelength'],quality['critical_path_delay_ns'])==(frozen_quality['total_wirelength'],frozen_quality['critical_path_delay_ns'])
  observed=observation(D/'initial');baseline,_=tree(case['native_tree']);baseline_cross=cross(baseline)
  assert baseline_cross==state['baseline_crossings']
  assert protocol['maximum_nets']==8
  order=sorted(current,key=lambda net:(-(sum(lengths[v] for v in current[net])-sum(lengths[v] for v in baseline[net])),net))[:8]
  assert len(state['steps'])<=len(order) and [v['net'] for v in state['steps']]==order[:len(state['steps'])]
  if len(state['steps'])<len(order):
   assert state.get('termination_reason')=='joint_baseline_met'
   assert state['current_quality']['total_wirelength']<=case['baseline_wirelength'] and state['current_quality']['critical_path_delay_ns']<=case['baseline_cpd_ns']
  order=order[:len(state['steps'])]
  current_tree=D/'initial/route.route_trees.csv';accepted=0;native_calls=1
  for rank,step in enumerate(state['steps']):
   net=step['net'];assert step['rank']==rank
   limit=max(Decimal(str(case['baseline_cpd_ns'])),Decimal(str(quality['critical_path_delay_ns'])));limit_ps=int(limit*1000)
   other_cross=cross({n:p for n,p in current.items() if n!=net})
   assert step['net_crossing_budget']==baseline_cross-other_cross>=0
   expected_order=sorted(by_net[net],key=lambda t:(-observed[t]['criticality_q'],t))
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
     expected_accept=(Decimal(str(q['critical_path_delay_ns']))<=limit and q['total_wirelength']<=quality['total_wirelength'] and (q['total_wirelength']<quality['total_wirelength'] or q['critical_path_delay_ns']<quality['critical_path_delay_ns']))
     if expected_accept:
      current=candidate;quality=q;observed=observation(directory);current_tree=directory/'route.route_trees.csv';accepted+=1
   assert step['accepted']==expected_accept,(label,rank)
  assert accepted==state['accepted'] and state['current_quality']==quality
  assert Path(state['current_tree']).resolve()==current_tree.resolve() and state['final_crossings']==cross(current)
  # Reconstruct every final connection, capacities and original graph edges.
  nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()));resources=list(struct.iter_unpack('<HHHHII',Path(case['input_prefix']+'.resources').read_bytes()));occupancy=collections.Counter()
  for net,parent in current.items():
   occupancy.update(set(parent)|{sources[net]})
   for task in by_net[net]:
    source=int(tasks[task]['source']);v=int(tasks[task]['sink']);visited=set()
    while v!=source:
     assert v in parent and v not in visited;visited.add(v);u=parent[v];start,count,_=nodes[u];assert any(dst==v for dst,_,w in edges[start:start+count]);v=u
    assert len(visited)<=int(tasks[task]['max_hops'])
  assert all(n<=resources[v][1] for v,n in occupancy.items())
  outcomes.append(dict(case=label,nets_visited=len(order),accepted=accepted,native_calls=native_calls,wirelength=quality['total_wirelength'],cpd_ns=quality['critical_path_delay_ns'],crossings=cross(current),joint_baseline_pass=quality['total_wirelength']<=case['baseline_wirelength'] and quality['critical_path_delay_ns']<=case['baseline_cpd_ns'] and cross(current)<=baseline_cross))
 sha(Path(__file__).resolve());report=dict(status='adaptive_parent_joint_budget_sweep_decisions_and_connectivity_replayed',outcomes=outcomes,source_sha256=refs,adopted=False,research_complete=False,scope='Posterior bounded cleanup, top8 initial per-net wirelength excesses, stop on joint pass; native acceptance replay and root-inclusive final capacity. Not prospective result, independent rerun or hardware performance.')
 with (P/'independent_audit.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=outcomes)))
if __name__=='__main__':main()
