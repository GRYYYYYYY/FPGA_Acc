"""Observer-only counters; reverse substitutions reproduce exact archived kernel."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];B=R/'build/native_bounded_wire_diag_v1_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 B.mkdir(exist_ok=False);p=R/'tools/native_bounded_wire_search_v1.cpp';original=p.read_text();s=original;edits=[]
 def replace(old,new):
  nonlocal s
  assert s.count(old)==1,old;s=s.replace(old,new);edits.append([old,new])
 replace('#include <cstdint>','#include <cstdint>\n#include <array>')
 replace('std::vector<U> path;};','std::vector<U> path;std::array<U,22> diag{};};')
 replace('c.path.clear();*out=', 'c.path.clear();c.diag.fill(0);*out=')
 replace('queue.emplace(0,initial,source,0);','queue.emplace(0,initial,source,0);c.diag[kept[source]?0:1]++;c.diag[2]++;c.diag[16]++;c.diag[18]=1;')
 replace('out->path_size=c.path.size();return 0;','out->path_size=c.path.size();for(const auto& l:labels)c.diag[l.alive?20:21]++;return 0;')
 replace('out->expanded++;','out->expanded++;c.diag[kept[node]?4:5]++;c.diag[objective==0?6:7]++;')
 replace('if(outside[dest]>=c.cap[dest])continue;','if(outside[dest]>=c.cap[dest]){c.diag[8]++;continue;}')
 replace('if(parent_source[dest]&&(parent_source[dest]!=node+1||parent_switch[dest]!=c.sw[i]+1))continue;','if(parent_source[dest]&&(parent_source[dest]!=node+1||parent_switch[dest]!=c.sw[i]+1)){c.diag[9]++;continue;}')
 replace('if(c.inc[i]>budget-delay||w>=bound-objective)continue;','if(c.inc[i]>budget-delay||w>=bound-objective){if(c.inc[i]>budget-delay)c.diag[10]++;if(w>=bound-objective)c.diag[11]++;continue;}')
 replace('if(dominated)continue;','if(dominated){c.diag[12]++;continue;}')
 replace('if(labels.size()>=max_labels)return finish(2);','if(labels.size()>=max_labels){c.diag[13]=objective;c.diag[14]=delay;c.diag[15]=node;return finish(2);}')
 replace('std::vector<U> keep;keep.reserve(old.size()+1);','if(old.empty())c.diag[16]++;else c.diag[17]++;std::vector<U> keep;keep.reserve(old.size()+1);')
 replace('old.swap(keep);queue.emplace(nc,nd,dest,next);','old.swap(keep);c.diag[kept[dest]?0:1]++;c.diag[nc==0?2:3]++;c.diag[18]=std::max(c.diag[18],U(old.size()));if(old.size()>1)c.diag[19]++;queue.emplace(nc,nd,dest,next);')
 extra='\nextern "C" uint64_t rc_diag_count(void* ptr,uint64_t index){return index<22?static_cast<Context*>(ptr)->diag[index]:0;}\n';s+=extra;restored=s[:-len(extra)]
 for old,new in reversed(edits):assert restored.count(new)==1;restored=restored.replace(new,old)
 assert restored==original
 clone=B/'kernel.cpp';clone.write_text(s);lib=B/'libroutecast_bounded.so';cmd=['g++','-std=c++17','-O3','-shared','-fPIC','-Wall','-Wextra','-Werror',str(clone),'-o',str(lib)];subprocess.run(cmd,check=True)
 (B/'receipt.json').write_text(json.dumps(dict(bindings={str(q):sha(q) for q in [p,clone,lib,pathlib.Path(__file__).resolve()]},command=cmd,observer_only_roundtrip_exact=True,reverse_substitutions=edits,scope='Counters only; original branch/queue/dominance/bounds retained. Behavioral parity on actual queries remains required.'),indent=2)+'\n');print('COMPILED_OBSERVER_ONLY_ROUNDTRIP_EXACT')
if __name__=='__main__':main()
