"""Read-only release sensitivity; posterior owner IDs never enter the router."""
import collections,csv,hashlib,heapq,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1]
P=R/'work/sb3_ex5p_single_owner_release_20261015'

def main():
 P.mkdir(exist_ok=False);bindings={}
 def read(path):
  path=Path(path);data=path.read_bytes();bindings[str(path)]=hashlib.sha256(data).hexdigest();return data
 frontier=json.loads(read(R/'work/sb3_ex5p_delay_frontier_20261015/independent_audit.json'))
 verified=json.loads(read(R/'work/sb3_ex5p_delay_frontier_20261015/frontier_rebuild_audit.json'))
 for path,expected in verified['source_sha256'].items():
  read(path);assert bindings[str(Path(path))]==expected,path
 protocol=json.loads(read(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json'))
 case=next(v for v in protocol['cases'] if v['label']=='ex5p')
 nodes=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.nodes')))
 edges=list(struct.iter_unpack('<IHH',read(case['input_prefix']+'.edges')))
 outcomes=[]
 for arm in frontier['outcomes']:
  directory=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm['arm']+'_0')
  owners=collections.defaultdict(set)
  for row in csv.DictReader(read(directory/'route.route_trees.csv').decode().splitlines()):
   if int(row['net_id'])==138:continue
   for key in ['parent','child']:
    if row[key]!=row['source']:owners[int(row[key])].add(int(row['net_id']))
  resources=list(struct.iter_unpack('<HHHHII',read(directory/'route.resources')))
  def solve(released):
   allowed=[len(owners[v]-released)<r[1] for v,r in enumerate(resources)]
   assert allowed[43804] and allowed[14256]
   distances={43804:0};parents={};pending=[(0,43804)];expanded=0
   while pending:
    value,u=heapq.heappop(pending)
    if distances[u]!=value:continue
    expanded+=1
    if u==14256:
     path=[u]
     while path[-1]!=43804:path.append(parents[path[-1]])
     return dict(optimum_ps=value,path=list(reversed(path)),expanded=expanded)
    start,count,_=nodes[u]
    for v,_,w in edges[start:start+count]:
     if allowed[v] and value+w<distances.get(v,1<<63):
      distances[v]=value+w;parents[v]=u;heapq.heappush(pending,(value+w,v))
   return dict(optimum_ps=None,path=[],expanded=expanded)
  baseline=solve(set());assert baseline['optimum_ps']==(644 if arm['arm']=='feedback_off' else 729)
  singles=[]
  for owner in arm['competing_nets']:
   result=solve({owner['id']});singles.append(dict(owner=owner,**result,target_reached=result['optimum_ps'] is not None and result['optimum_ps']<=567))
  union=solve({v['id'] for v in arm['competing_nets']})
  outcomes.append(dict(arm=arm['arm'],fixed_other_nets=baseline,single_owner_releases=singles,
   single_owner_target_successes=sum(v['target_reached'] for v in singles),frontier_owner_union_release=union))
 read(Path(__file__).resolve())
 report=dict(status='single_owner_release_relaxed_delay_sensitivity_completed',outcomes=outcomes,source_sha256=bindings,
  adopted=False,research_complete=False,scope='Posterior ex5p fixed-route packed-delay diagnostic. Removing an owner does not reroute that net or prove global feasibility/CPD. Owner union is not guaranteed sufficient or minimum. No paths or net IDs supplied to router.')
 with (P/'result.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps([dict(arm=v['arm'],single_owner_target_successes=v['single_owner_target_successes'],union_optimum_ps=v['frontier_owner_union_release']['optimum_ps'],best_single_ps=min(x['optimum_ps'] for x in v['single_owner_releases'] if x['optimum_ps'] is not None)) for v in outcomes]))
if __name__=='__main__':main()
