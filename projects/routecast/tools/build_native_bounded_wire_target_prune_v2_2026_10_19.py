"""Exact reverse reachability under unchanged capacity/parent predicates."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];B=R/'build/native_bounded_wire_target_prune_v2_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 B.mkdir(exist_ok=False);p=R/'tools/native_bounded_wire_search_v1.cpp';s=p.read_text();s=s.replace('#include <cstdint>','#include <cstdint>\n#include <memory>\n#include <array>');s=s.replace('std::vector<U> path;};','std::vector<U> path;std::vector<U> rrow{},rsource{},rslot{};std::array<U,3> reverse_stats{};};')
 old='return new Context{n,m,row,dest,eid,sw,inc,cap,length,{}};'
 new='''auto c=std::unique_ptr<Context>(new Context{n,m,row,dest,eid,sw,inc,cap,length,{}});
 c->rrow.assign(n+1,0);c->rsource.resize(m);c->rslot.resize(m);
 for(U i=0;i<m;i++)c->rrow[dest[i]+1]++;
 for(U v=0;v<n;v++)c->rrow[v+1]+=c->rrow[v];
 auto position=c->rrow;
 for(U u=0;u<n;u++)for(U e=row[u];e<row[u+1];e++){U j=position[dest[e]]++;c->rsource[j]=u;c->rslot[j]=e;}
 return c.release();'''
 assert old in s;s=s.replace(old,new);s=s.replace('c.path.clear();*out=', 'c.path.clear();c.reverse_stats.fill(0);*out=')
 needle='if(initial>budget||!bound)return 0;'
 add='''
  // Reverse reachability ignores both RC and wire bounds. Every admissible
  // forward budget path is retained, so this is an exact relaxation filter.
  std::vector<uint8_t> reachable(c.n,0);std::vector<U> reverse_queue;
  reachable[sink]=1;reverse_queue.push_back(sink);
  for(U cursor=0;cursor<reverse_queue.size();cursor++){
   U b=reverse_queue[cursor];
   if(outside[b]>=c.cap[b])continue;
   for(U j=c.rrow[b];j<c.rrow[b+1];j++){
    c.reverse_stats[1]++;U a=c.rsource[j],e=c.rslot[j];
    if(parent_source[b]&&(parent_source[b]!=a+1||parent_switch[b]!=c.sw[e]+1))continue;
    if(!reachable[a]){reachable[a]=1;reverse_queue.push_back(a);}
   }
  }
  c.reverse_stats[0]=reverse_queue.size();
  if(!reachable[source])return 0;
'''
 assert s.count(needle)==1;s=s.replace(needle,needle+add);needle='U dest=c.dest[i];if(outside[dest]>=c.cap[dest])continue;';assert s.count(needle)==1;s=s.replace(needle,'U dest=c.dest[i];if(!reachable[dest]){c.reverse_stats[2]++;continue;}if(outside[dest]>=c.cap[dest])continue;');s+='\nextern "C" uint64_t rc_reverse_count(void* ptr,uint64_t index){return index<3?static_cast<Context*>(ptr)->reverse_stats[index]:0;}\n'
 clone=B/'kernel.cpp';clone.write_text(s);lib=B/'libroutecast_bounded.so';cmd=['g++','-std=c++17','-O3','-shared','-fPIC','-Wall','-Wextra','-Werror',str(clone),'-o',str(lib)];subprocess.run(cmd,check=True)
 (B/'receipt.json').write_text(json.dumps(dict(bindings={str(q):sha(q) for q in [p,clone,lib,pathlib.Path(__file__).resolve()]},command=cmd,scope='Prune only nodes unable to reach sink using same capacity and fixed-parent rules, without any RC/wire relaxation or increased Pareto label limit. Reverse graph setup/query costs must be included separately; no runtime gain claim.'),indent=2)+'\n');print('TARGET_REACHABILITY_PRUNE_COMPILED')
if __name__=='__main__':main()
