"""Isolated observer after actual native seed read, exits before timing/search."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
B=R/'build/native_external_initial_response_observer_v2_2026-10-19';D=R/'build/native_external_seed_import_probe_v1_2026-10-19'
def main():
 b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/route.cpp';s=f.read_text();anchor='        VTR_LOG("ROUTECAST NET-aware seed imported feasible=%d with actual router options\\n", int(feasible));';assert s.count(anchor)==1
 code=r'''
        if(std::getenv("ROUTECAST_IMPORT_ONLY")) {
            FILE* obs=std::fopen("native_import.tsv","wx");if(!obs)throw std::runtime_error("import observer open");
            size_t selected=0,pins=0,required=0;
            std::fprintf(obs,"H\t1\t%d\n",int(feasible));
            for(auto net:net_list.nets()) {
                bool ignored=net_list.net_is_ignored(net);const auto& tree=route_ctx.route_trees[net];
                std::fprintf(obs,"T\t%zu\t%d\t%d\t%zu\t%zu\n",size_t(net),int(ignored),int(bool(tree)),size_t(route_ctx.net_rr_terminals[net][0]),tree?size_t(tree->root().inode):size_t(-1));
                if(!ignored)required+=net_list.net_pins(net).size()-1;
                if(!tree)continue;
                if(ignored)throw std::runtime_error("ignored seed tree unexpected");
                if(tree->root().inode!=route_ctx.net_rr_terminals[net][0])throw std::runtime_error("seed SOURCE mismatch");
                ++selected;
                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                    auto sink=tree->find_by_isink(pin);
                    if(!sink || sink->inode!=route_ctx.net_rr_terminals[net][pin])throw std::runtime_error("seed native pin/SINK mismatch");
                    std::fprintf(obs,"P\t%zu\t%zu\t%zu\n",size_t(net),pin,size_t(sink->inode));++pins;
                }
                for(const auto& node:tree->all_nodes())std::fprintf(obs,"N\t%zu\t%zu\n",size_t(net),size_t(node.inode));
            }
            const auto& graph=device_ctx.rr_graph;
            for(auto node:graph.nodes())std::fprintf(obs,"O\t%zu\t%d\t%d\n",size_t(node),route_ctx.rr_node_route_inf[node].occ(),int(graph.node_capacity(node)));
            std::fprintf(obs,"F\t%zu\t%zu\t%zu\n",selected,pins,required);
            if(std::fclose(obs))throw std::runtime_error("import observer close");
            VTR_LOG("RC_IMPORT_ONLY_VERIFIED selected_NETs=%zu selected_pins=%zu required_pins=%zu exit_before_timing_search=1\n",selected,pins,required);
            std::fflush(nullptr);std::exit(0);
        }
'''
 s=s.replace(anchor,anchor+code);f.write_text(s);compile=[x.replace(str(B)+'/',str(D)+'/') for x in p['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for q in (D/'source').rglob('*'):
  if q.is_file():bindings[str(q)]=sha(q)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Read actual imported route trees, native isink/terminal identity, RR occupancy, full required demand. Probe exit before lookahead timing and router search, not VPR FULL/canonical/STA result.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='SEED_IMPORT_ONLY_PROBE_BUILT_RUNTIME_ADMISSION_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('SEED_IMPORT_PROBE_BUILT')
if __name__=='__main__':main()
