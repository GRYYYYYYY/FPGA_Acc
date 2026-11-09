"""Extend verified observer with exact sorted per-iteration CHANNEL support sets."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
B=R/'build/native_external_initial_response_observer_v2_2026-10-19';D=R/'build/native_external_iteration_support_observer_v1_2026-10-19'
def main():
 b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/route.cpp';s=f.read_text();anchor='        RouteIterResults iter_results = netlist_router->route_netlist(itry, pres_fac, worst_negative_slack);';assert s.count(anchor)==1;s=s.replace(anchor,anchor+r'''
        {
            FILE* trace=std::fopen("iteration_support.tsv",itry==1?"wx":"a");
            if(!trace)throw std::runtime_error("iteration support open");
            for(auto net:net_list.nets()) {
                if(net_list.net_is_ignored(net))continue;
                std::vector<size_t> nodes;
                if(route_ctx.route_trees[net])for(const auto& node:route_ctx.route_trees[net]->all_nodes()) {
                    auto type=device_ctx.rr_graph.node_type(node.inode);
                    if(type==CHANX || type==CHANY)nodes.push_back(size_t(node.inode));
                }
                std::sort(nodes.begin(),nodes.end());
                nodes.erase(std::unique(nodes.begin(),nodes.end()),nodes.end());
                std::fprintf(trace,"%d\t%zu\t%zu",itry,size_t(net),nodes.size());
                for(auto n:nodes)std::fprintf(trace,"\t%zu",n);
                std::fputc('\n',trace);
            }
            if(std::fclose(trace))throw std::runtime_error("iteration support close");
        }
''');f.write_text(s);compile=[x.replace(str(B)+'/',str(D)+'/') for x in p['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for q in (D/'source').rglob('*'):
  if q.is_file():bindings[str(q)]=sha(q)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Exact sorted unique CHANNEL sets after route_netlist each iteration, before local OPIN reservation. No hash collisions. Runtime/physical equivalence pending; diagnostic overhead not speedup.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='EXACT_ITERATION_SUPPORT_OBSERVER_BUILT_EQUIVALENCE_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('ITERATION_SUPPORT_OBSERVER_BUILT')
if __name__=='__main__':main()
