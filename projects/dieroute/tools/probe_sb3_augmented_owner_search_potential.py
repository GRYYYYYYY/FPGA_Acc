"""Apply generic one-owner state search to frozen native development graphs."""
import collections,csv,hashlib,heapq,json,struct
from pathlib import Path
from single_owner_exchange_search import search
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'work/sb3_augmented_owner_search_potential_20261015';out.mkdir(exist_ok=False);refs={}
 def read(path):
  path=Path(path);data=path.read_bytes();refs[str(path)]=hashlib.sha256(data).hexdigest();return data
 p=json.loads(read(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
 case=next(c for c in p['cases'] if c['label']=='ex5p')
 nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')))
 reverse=[[] for _ in nodes]
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:reverse[v].append((u,w))
 infinity=1<<63;suffix=[infinity]*len(nodes);suffix[14256]=0;pending=[(0,14256)]
 while pending:
  value,u=heapq.heappop(pending)
  if value!=suffix[u]:continue
  for v,w in reverse[u]:
   if value+w<suffix[v]:suffix[v]=value+w;heapq.heappush(pending,(value+w,v))
 assert suffix[14256]==0
 checked=0
 for u,(begin,count,_) in enumerate(nodes):
  for v,_,w in edges[begin:begin+count]:
   if suffix[v]!=infinity:assert suffix[u]<=w+suffix[v];checked+=1
 parent=json.loads(read(R/'work/sb3_augmented_owner_search_20261015/result.json'))
 outcomes=[]
 for arm in ['feedback_off','feedback_on']:
  d=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0')
  owners=[set() for _ in nodes]
  for row in csv.DictReader(read(d/'route.route_trees.csv').decode().splitlines()):
   if row['child']!=row['source']:owners[int(row['child'])].add(int(row['net_id']))
  resources=list(struct.iter_unpack('<HHHHII',read(d/'route.resources')))
  result=search(nodes,edges,[r[1] for r in resources],owners,43804,14256,138,567,suffix_lower_bound=suffix)
  assert result['found'] and result['delay']==(460 if arm=='feedback_off' else 562),result
  path=result['path_nodes'];release=result['released_owner']
  assert len(set(path))==len(path)
  assert all(len(owners[v]-{138,release})<resources[v][1] for v in path)
  assert len(result['path_edges'])==len(path)-1
  for u,v,index in zip(path,path[1:],result['path_edges']):
   start,count,_=nodes[u];assert start<=index<start+count and edges[index][0]==v
  previous=next(v for v in parent['outcomes'] if v['arm']==arm)
  assert result['delay']==previous['delay']
  outcomes.append(dict(arm=arm,previous_expanded=previous['expanded'],previous_states=previous['discovered_states'],**result))
 for f in [Path(__file__).resolve(),Path(__file__).with_name('single_owner_exchange_search.py')]:read(f)
 report=dict(status='certified_suffix_preserves_native_one_owner_optima_and_reduces_search',suffix_edge_inequalities_checked=checked,outcomes=outcomes,source_sha256=refs,
  adopted=False,research_complete=False,scope='Posterior target selection remains diagnostic. Search dynamically chooses owner without recorded candidate IDs; packed delay only, no net repair or global native quality. Suffix setup and certificate scan are additional charged CPU work; fewer expanded states alone do not establish end-to-end speedup.')
 (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps([{k:v for k,v in x.items() if k not in ['path_nodes','path_edges']} for x in outcomes]))
if __name__=='__main__':main()
