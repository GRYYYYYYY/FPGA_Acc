"""Export actual imported full-tree Tdel with current corrected native link."""
import json,shutil,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19'
D=R/'build/native_external_tree_delay_probe_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text())
 latest=R/'build/native_external_shared_sink_native_v1_2026-10-19/protocol.json'
 q=json.loads(latest.read_text())
 assert all(sha(k)==v for k,v in q['bindings'].items())
 D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source')
 f=D/'source/route.cpp';s=f.read_text()
 anchor='        VTR_LOG("ROUTECAST NET-aware seed imported feasible=%d with actual router options\\n", int(feasible));'
 code='\n        if(std::getenv("ROUTECAST_IMPORT_ONLY")) {\n            FILE* obs=std::fopen("native_import.tsv","wx");if(!obs)throw std::runtime_error("import observer open");\n            size_t selected=0,pins=0,required=0;\n            std::fprintf(obs,"H\\t1\\t%d\\n",int(feasible));\n            for(auto net:net_list.nets()) {\n                std::fprintf(obs,"NAME\\t%zu\\t%s\\n",size_t(net),net_list.net_name(net).c_str()); bool ignored=net_list.net_is_ignored(net);const auto& tree=route_ctx.route_trees[net];\n                std::fprintf(obs,"T\\t%zu\\t%d\\t%d\\t%zu\\t%zu\\n",size_t(net),int(ignored),int(bool(tree)),size_t(route_ctx.net_rr_terminals[net][0]),tree?size_t(tree->root().inode):size_t(-1));\n                if(!ignored)required+=net_list.net_pins(net).size()-1;\n                if(!tree)continue;\n                if(ignored)throw std::runtime_error("ignored seed tree unexpected");\n                if(tree->root().inode!=route_ctx.net_rr_terminals[net][0])throw std::runtime_error("seed SOURCE mismatch");\n                ++selected;\n                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {\n                    auto sink=tree->find_by_isink(pin);\n                    if(!sink || sink->inode!=route_ctx.net_rr_terminals[net][pin])throw std::runtime_error("seed native pin/SINK mismatch");\n                    std::fprintf(obs,"P\\t%zu\\t%zu\\t%zu\\n",size_t(net),pin,size_t(sink->inode)); std::fprintf(obs,"D\\t%zu\\t%zu\\t%.9g\\n",size_t(net),pin,double(sink->Tdel));++pins;\n                }\n                for(const auto& node:tree->all_nodes())std::fprintf(obs,"N\\t%zu\\t%zu\\n",size_t(net),size_t(node.inode));\n            }\n            const auto& graph=device_ctx.rr_graph;\n            for(auto node:graph.nodes())std::fprintf(obs,"O\\t%zu\\t%d\\t%d\\n",size_t(node),route_ctx.rr_node_route_inf[node].occ(),int(graph.node_capacity(node)));\n            std::fprintf(obs,"F\\t%zu\\t%zu\\t%zu\\n",selected,pins,required);\n            if(std::fclose(obs))throw std::runtime_error("import observer close");\n            VTR_LOG("RC_IMPORT_ONLY_VERIFIED selected_NETs=%zu selected_pins=%zu required_pins=%zu exit_before_timing_search=1\\n",selected,pins,required);\n            std::fflush(nullptr);std::exit(0);\n        }\n'
 assert s.count(anchor)==1;s=s.replace(anchor,anchor+code);f.write_text(s)
 compile=[x.replace(str(B),str(D)) for x in p['compile']]
 link=[x.replace(str(B/'route.o'),str(D/'route.o')).replace(str(latest.parent/'sequence_vpr'),str(D/'sequence_vpr')) for x in q['link']]
 bindings={str(latest):sha(latest),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for x in (D/'source').rglob('*'):
  if x.is_file():bindings[str(x)]=sha(x)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==v for k,v in bindings.items())
 (D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n')
 print('TREE_DELAY_PROBE_BUILT',flush=True)
if __name__=='__main__':main()
