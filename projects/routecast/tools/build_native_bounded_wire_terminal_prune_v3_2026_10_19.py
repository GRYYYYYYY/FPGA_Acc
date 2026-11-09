"""Exact cheap dead-end/one-hop terminal filter; no per-query reverse traversal."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];B=R/'build/native_bounded_wire_terminal_prune_v3_2026-10-19'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 B.mkdir(exist_ok=False);p=R/'tools/native_bounded_wire_search_v1.cpp';s=p.read_text().replace('#include <cstdint>','#include <cstdint>\n#include <memory>');s=s.replace('std::vector<U> path;};','std::vector<U> path;std::vector<uint8_t> terminal_only{};U terminal_pruned=0,terminal_examined=0;};')
 old='return new Context{n,m,row,dest,eid,sw,inc,cap,length,{}};'
 new='''auto c=std::unique_ptr<Context>(new Context{n,m,row,dest,eid,sw,inc,cap,length,{}});
 c->terminal_only.assign(n,1);
 for(U v=0;v<n;v++)for(U e=row[v];e<row[v+1];e++)if(row[dest[e]]!=row[dest[e]+1]){c->terminal_only[v]=0;break;}
 return c.release();'''
 assert old in s;s=s.replace(old,new);s=s.replace('c.path.clear();*out=','c.path.clear();c.terminal_pruned=0;c.terminal_examined=0;*out=');old='U dest=c.dest[i];if(outside[dest]>=c.cap[dest])continue;';new='''U dest=c.dest[i];
    // If dest is not the target and every outgoing neighbor has zero
    // outdegree, only a direct edge to the target can permit completion.
    if(dest!=sink&&c.terminal_only[dest]){
     bool reaches=false;
     for(U j=c.row[dest];j<c.row[dest+1];j++){c.terminal_examined++;if(c.dest[j]==sink){reaches=true;break;}}
     if(!reaches){c.terminal_pruned++;continue;}
    }
    if(outside[dest]>=c.cap[dest])continue;''';assert old in s;s=s.replace(old,new);s+='\nextern "C" uint64_t rc_terminal_count(void* ptr,uint64_t index){auto& c=*static_cast<Context*>(ptr);return index==0?c.terminal_pruned:(index==1?c.terminal_examined:(index==2?c.terminal_only.size():0));}\n';clone=B/'kernel.cpp';clone.write_text(s);lib=B/'libroutecast_bounded.so';cmd=['g++','-std=c++17','-O3','-shared','-fPIC','-Wall','-Wextra','-Werror',str(clone),'-o',str(lib)];subprocess.run(cmd,check=True)
 (B/'receipt.json').write_text(json.dumps(dict(bindings={str(q):sha(q) for q in [p,clone,lib,pathlib.Path(__file__).resolve()]},command=cmd,scope='Exact structural dead-end pruning independent of capacities/parents/RC, therefore weaker than full reverse reachability. Same budget and Pareto label limits. One static uint8 flag per node; no reverse CSR or per-query reachability allocation. No runtime claim pending paired replay.'),indent=2)+'\n');print('TERMINAL_FILTER_COMPILED')
if __name__=='__main__':main()
