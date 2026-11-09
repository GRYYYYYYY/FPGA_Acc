"""Profile actual native routed multi-layer paths, retaining revisits and shared edges."""
import collections,csv,hashlib,json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def profile(directory):
 files=[directory/k for k in ['connections.csv','native_tree.csv','topology.node_die']]
 owners=[v[0] for v in struct.iter_unpack('<H',files[2].read_bytes())]
 parents={};edge_set=set();net_sources={}
 for row in csv.DictReader(files[1].open()):
  net,source,parent,child=(int(row[k]) for k in ['net_id','source','parent','child'])
  assert 0<=parent<len(owners) and 0<=child<len(owners)
  assert parent!=child and (net,child) not in parents
  parents[net,child]=parent;edge_set.add((net,parent,child))
  assert net not in net_sources or net_sources[net]==source
  net_sources[net]=source
 pairs=collections.Counter();hops=collections.Counter();minimum=collections.Counter();detours=collections.Counter();traces=collections.Counter();used=set();tasks=0
 for row in csv.DictReader(files[0].open()):
  net,source,sink=(int(row[k]) for k in ['net_id','source','sink'])
  assert net_sources[net]==source
  current=sink;seen=set();back=[sink]
  while current!=source:
   assert current not in seen,(net,current,'cycle');seen.add(current)
   parent=parents[net,current];used.add((net,parent,current));back.append(parent);current=parent
  trace=[]
  for node in reversed(back):
   if not trace or trace[-1]!=owners[node]:trace.append(owners[node])
  count=len(trace)-1;lower=abs(owners[source]-owners[sink])
  assert count>=lower and all(abs(a-b)==1 for a,b in zip(trace,trace[1:]))
  pairs[f'{owners[source]}->{owners[sink]}']+=1;hops[count]+=1;minimum[lower]+=1;detours[count-lower]+=1;traces['>'.join(map(str,trace))]+=1;tasks+=1
 assert used==edge_set,('uncovered_tree_edges',len(edge_set-used))
 cross={(n,a,b) for n,a,b in edge_set if owners[a]!=owners[b]}
 return dict(case=directory.name,tasks=tasks,nets=len(net_sources),tree_edges=len(edge_set),unique_net_cross_edges=len(cross),endpoint_layer_pairs=dict(sorted(pairs.items())),actual_crossing_hops=dict(sorted(hops.items())),minimum_adjacent_layer_hops=dict(sorted(minimum.items())),excess_crossings=dict(sorted(detours.items())),layer_traces=dict(sorted(traces.items())),source_sha256={str(q):sha(q) for q in files})
def main():
 p=ROOT/'work/sb_native_roundtrip_preflight_20261015'
 protocol=json.loads((p/'protocol.json').read_text());rows=[profile(p/c['label']) for c in protocol['cases']]
 report=dict(status='six_native_full_tree_multilayer_path_profiles_checked',cases=rows,source_sha256={str(Path(__file__).resolve()):sha(__file__),str(p/'protocol.json'):sha(p/'protocol.json')},scope='Actual original native VPR tree paths for every exported source/sink; unique tree edges, endpoint pairs, adjacent-layer crossing counts and revisits. Shared edges counted once per net in unique totals and once per task in path histograms. Abstract SB model; no physical SLL, capacity or algorithm improvement claim.',board_result=False,research_complete=False)
 out=ROOT/'work/sb_native_layer_path_profiles_20261015';out.mkdir(exist_ok=False)
 (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps([dict(case=r['case'],tasks=r['tasks'],actual_crossing_hops=r['actual_crossing_hops'],minimum_adjacent_layer_hops=r['minimum_adjacent_layer_hops'],unique_net_cross_edges=r['unique_net_cross_edges']) for r in rows],indent=2))
if __name__=='__main__':main()
