"""Read-only actual NET invocation snapshots, both phases retain old path resources."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_target_iteration_observer_v1_2026-10-19';D=R/'build/native_external_growth_owner_observer_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text());b=json.loads((B/'receipt.json').read_text());assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in p['bindings'].items());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/overlay/SerialNetlistRouter.tpp';s=f.read_text()
 anchor='        NetResultFlags flags = route_net(';assert s.count(anchor)==1
 code=r'''
        const int target_pin=size_t(net_id)==90?19:size_t(net_id)==83?40:size_t(net_id)==368?2:0;
        const bool observe_growth=target_pin && (itry==36 || itry==38 || itry==50);
        std::vector<size_t> watched;
        auto watch_path=[&]() {
            if(!route_ctx.route_trees[net_id])return;
            auto sink=route_ctx.route_trees[net_id]->find_by_isink(target_pin);
            if(!sink)return;
            const RouteTreeNode* node=&sink.value();
            while(node) {watched.push_back(size_t(node->inode));auto parent=node->parent();node=parent?&parent.value():nullptr;}
        };
        auto growth_snapshot=[&](char phase) {
            if(!observe_growth)return;
            watch_path();std::sort(watched.begin(),watched.end());watched.erase(std::unique(watched.begin(),watched.end()),watched.end());
            FILE* f=std::fopen("growth_owners.tsv","a");if(!f)throw std::runtime_error("growth owner open");
            float crit=calculate_clb_net_pin_criticality(*_timing_info,_netlist_pin_lookup,_net_list.net_pin(net_id,target_pin),_is_flat);
            std::fprintf(f,"Q\t%c\t%d\t%zu\t%zu\t%d\t%.9g\t%.9g\t%.9g\n",phase,itry,inet,size_t(net_id),target_pin,double(_net_delay[net_id][target_pin]),double(crit),double(pres_fac));
            const auto& graph=g_vpr_ctx.device().rr_graph;
            for(auto n:watched) {
                auto rr=RRNodeId(n);
                std::fprintf(f,"N\t%c\t%d\t%zu\t%zu\t%zu\t%d\t%d\t%.9g\t%.9g\n",phase,itry,inet,size_t(net_id),n,route_ctx.rr_node_route_inf[rr].occ(),int(graph.node_capacity(rr)),double(route_ctx.rr_node_route_inf[rr].acc_cost),double(get_single_rr_cong_pres_cost(rr,pres_fac)));
            }
            for(auto owner:_net_list.nets())if(route_ctx.route_trees[owner]) {
                std::vector<size_t> owned;
                for(const auto& node:route_ctx.route_trees[owner]->all_nodes())if(std::binary_search(watched.begin(),watched.end(),size_t(node.inode)))owned.push_back(size_t(node.inode));
                std::sort(owned.begin(),owned.end());owned.erase(std::unique(owned.begin(),owned.end()),owned.end());
                for(auto n:owned)std::fprintf(f,"O\t%c\t%d\t%zu\t%zu\t%zu\t%zu\t%s\n",phase,itry,inet,size_t(net_id),n,size_t(owner),_net_list.net_name(owner).c_str());
            }
            if(std::fclose(f))throw std::runtime_error("growth owner close");
        };
        growth_snapshot('B');
'''
 s=s.replace(anchor,code+anchor);a='            route_ctx.route_bb[net_id]);';assert s.count(a)==1;s=s.replace(a,a+"\n        growth_snapshot('A');");f.write_text(s)
 compile=[x.replace(str(B),str(D)) for x in p['compile']];link=[x.replace(str(B),str(D)) for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for f in (D/'source').rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Posthoc diagnosis fixed cross product NETs83/90/368 and iterations36/38/50, all3 botharms. Actual route_net invocation pre/post, Q delays/criticality; watched union of old and new target pin paths, perresource occupancy/cap/history/pres and all NET tree owners. Pre-call before router ripup, not connection-search inner frontier. Read-only, runtime equivalence pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT')
if __name__=='__main__':main()
