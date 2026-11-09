"""Exact reverse resource lower bound and Pareto A*; original budgets/label cap."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];O=R/'build/native_bounded_wire_astar_v4_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);B=R/'build/native_bounded_wire_target_prune_v2_2026-10-19';proof=B/'receipt.json';p=json.loads(proof.read_text())
 for name,h in p['bindings'].items():assert sha(pathlib.Path(name))==h
 original=B/'kernel.cpp';s=original.read_text();a=s.index('  // Reverse reachability');b=s.index('  const U none=',a)
 reverse='''  // Reverse Dijkstra relaxes RC only; its resource potential is exact for
  // the same capacity and fixed-parent edge predicates. Entering b costs
  // zero for kept nodes, otherwise length[b]. No Pareto labels are spent here.
  const U infinity=std::numeric_limits<U>::max();
  std::vector<U> lower(c.n,infinity);
  using ReverseKey=std::pair<U,U>;std::priority_queue<ReverseKey,std::vector<ReverseKey>,std::greater<ReverseKey>> reverse_queue;
  lower[sink]=0;reverse_queue.emplace(0,sink);
  while(!reverse_queue.empty()){
   auto [distance,b]=reverse_queue.top();reverse_queue.pop();if(lower[b]!=distance)continue;c.reverse_stats[0]++;
   if(outside[b]>=c.cap[b])continue;
   U weight=kept[b]?0:c.length[b];if(weight>=bound-distance)continue;
   for(U j=c.rrow[b];j<c.rrow[b+1];j++){
    c.reverse_stats[1]++;U a=c.rsource[j],e=c.rslot[j];
    if(parent_source[b]&&(parent_source[b]!=a+1||parent_switch[b]!=c.sw[e]+1))continue;
    U next=distance+weight;if(next<lower[a]){lower[a]=next;reverse_queue.emplace(next,a);}
   }
  }
  if(lower[source]==infinity)return 0;
'''
 s=s[:a]+reverse+s[b:];s=s.replace('queue.emplace(0,initial,source,0);','queue.emplace(lower[source],initial,source,0);');s=s.replace('auto [objective,delay,node,lid]=queue.top();queue.pop();if(!labels[lid].alive)continue;out->expanded++;','auto [estimate,delay,node,lid]=queue.top();queue.pop();(void)estimate;if(!labels[lid].alive)continue;U objective=labels[lid].cost;out->expanded++;');s=s.replace('if(!reachable[dest])','if(lower[dest]==infinity)');needle='U nd=delay+c.inc[i],nc=objective+w;auto& old=front[dest];';assert needle in s;s=s.replace(needle,'U nd=delay+c.inc[i],nc=objective+w;if(lower[dest]>=bound-nc){c.reverse_stats[2]++;continue;}auto& old=front[dest];');s=s.replace('queue.emplace(nc,nd,dest,next);','queue.emplace(nc+lower[dest],nd,dest,next);');assert 'reachable[' not in s;clone=O/'kernel.cpp';clone.write_text(s);lib=O/'libroutecast_bounded.so';cmd=['g++','-std=c++17','-O3','-shared','-fPIC','-Wall','-Wextra','-Werror',str(clone),'-o',str(lib)];subprocess.run(cmd,check=True);(O/'receipt.json').write_text(json.dumps(dict(bindings={str(q):sha(q) for q in [proof,original,clone,lib,pathlib.Path(__file__).resolve()]},command=cmd,scope='Reverse shortest resource potential ignores RC, retains all feasible budget paths. Pareto dominance and goals use actual cost/RC; heap primary is actual cost+potential. Same total-created Pareto label cap. Reverse-index and per-query Dijkstra costs are extra work, not a free speedup.'),indent=2)+'\n');print('PARETO_RESOURCE_ASTAR_BUILT')
if __name__=='__main__':main()
