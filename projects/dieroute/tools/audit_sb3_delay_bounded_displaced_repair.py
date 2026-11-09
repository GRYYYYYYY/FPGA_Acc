"""Check all repair orders against original native trees and delay caps."""
import collections,csv,hashlib,itertools,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_delay_bounded_displaced_repair_20261015'
def main():
 refs={}
 def bind(f):
  f=Path(f);h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(f)]=h.hexdigest();return h.hexdigest()
 def load(f):bind(f);return json.loads(Path(f).read_text())
 result=load(P/'result.json')
 for document in [result,load(P/'protocol.json'),load(P/'launch_protocol.json'),load(P/'input_bindings.json')]:
  for f,h in document['source_sha256'].items():assert bind(f)==h,f
 base=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015';case=load(base/'protocol.json')['case'];prior=load(base/'result.json')
 tasks={int(v['id']):v for v in csv.DictReader(Path(case['connections']).open())};by_net=collections.defaultdict(list)
 for task,row in tasks.items():by_net[int(row['net_id'])].append(task)
 nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()))
 def delay(source,path):
  total=0
  for v in path:
   start,count,_=nodes[source];weights=[w for dst,_,w in edges[start:start+count] if dst==v];assert weights
   total+=min(weights);source=v
  return total
 groups=[]
 for trial in prior['outcomes']:
  name=trial['label'];net=trial['displaced_net'];tree=base/name/'route.route_trees.csv';assert bind(tree)==trial['tree_sha256']
  old={int(v['child']):int(v['parent']) for v in csv.DictReader(tree.open()) if int(v['net_id'])==net}
  rows=[v for v in result['outcomes'] if v['parent_trial']==name]
  assert {tuple(v['order']) for v in rows}==set(itertools.permutations(sorted(by_net[net])))
  for row in rows:
   assert row['complete'] and all(v['status']=='optimal_path' for v in row['steps'])
   assert {int(v):u for v,u in row['parent'].items()}==old
   assert set(map(int,row['paths']))==set(by_net[net])
   for task in by_net[net]:
    source=int(tasks[task]['source']);v=int(tasks[task]['sink']);path=[]
    while v!=source:path.append(v);v=old[v];assert len(path)<=len(old)
    expected=list(reversed(path));assert row['paths'][str(task)]==expected
    value=delay(source,expected);step=next(v for v in row['steps'] if v['task']==task)
    assert value==step['delay_cap_ps']==step['delay']
   assert row['new_displaced_native_wire']==row['old_displaced_native_wire']
  validation=load(base/name/'native_validation/validation.json');assert validation['legal']
  groups.append(dict(parent_trial=name,orders=len(rows),all_canonical_trees_identical=True,native_wirelength_unchanged=validation['total_wirelength'],native_cpd_ns_unchanged=validation['critical_path_delay_ns']))
 assert sum(v['orders'] for v in groups)==len(result['outcomes'])==14
 bind(Path(__file__).resolve())
 audit=dict(status='all14_delay_bounded_repairs_exactly_reproduce_prior_native_exchange_trees',outcomes=groups,source_sha256=refs,
  new_native_runs=0,adopted=False,research_complete=False,
  scope='All14greedy sinkorders preserve each prior canonical displaced tree and every source-sink path under incumbent delaycaps. Fixed othernets imply unchanged complete native route semantics; prior native metrics retained, not newly measured. No global constrained Steiner optimum, looser-delay-budget impossibility or new quality improvement claim.')
 with (P/'independent_audit.json').open('x') as stream:json.dump(audit,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=audit['status'],outcomes=groups)))
if __name__=='__main__':main()
