"""Private complete RR frontier at exact round2 NET2 pre-call, no mutation."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
B=R/'build/native_external_early_net_observer_v1_2026-10-19';D=R/'build/native_external_full_rr_frontier_observer_v1_2026-10-19'
def main():
 b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/overlay/SerialNetlistRouter.tpp';s=f.read_text();anchor="        observe('B',inet,net_id);";assert s.count(anchor)==1
 code=r'''
        if(itry==2 && inet==1 && size_t(net_id)==2) {
            FILE* frontier=std::fopen("rr_frontier.tsv","wx");if(!frontier)throw std::runtime_error("RR frontier open");
            std::unique_ptr<FILE,decltype(&std::fclose)> frontier_guard(frontier,&std::fclose);
            const auto& graph=g_vpr_ctx.device().rr_graph;
            const auto& bb=route_ctx.route_bb[net_id];
            std::fprintf(frontier,"F\t%d\t%zu\t%zu\t%.9g\t%.9g\t%d\t%d\t%d\t%d\n",itry,inet,size_t(net_id),double(pres_fac),double(worst_neg_slack),bb.xmin,bb.xmax,bb.ymin,bb.ymax);
            for(auto id:graph.nodes()) {
                auto type=graph.node_type(id);
                const char* name=type==SOURCE?"SOURCE":type==SINK?"SINK":type==IPIN?"IPIN":type==OPIN?"OPIN":type==CHANX?"CHANX":type==CHANY?"CHANY":"UNKNOWN";
                std::fprintf(frontier,"N\t%zu\t%s\t%d\t%d\t%.9g\t%.9g\t%.9g\t%zu\n",size_t(id),name,int(graph.node_capacity(id)),route_ctx.rr_node_route_inf[id].occ(),double(route_ctx.rr_node_route_inf[id].acc_cost),double(get_single_rr_cong_base_cost(id)),double(get_single_rr_cong_pres_cost(id,pres_fac)),size_t(graph.node_cost_index(id)));
            }
            for(auto net:_net_list.nets()) {
                std::vector<size_t> nodes;
                if(route_ctx.route_trees[net])for(const auto& node:route_ctx.route_trees[net]->all_nodes())nodes.push_back(size_t(node.inode));
                std::sort(nodes.begin(),nodes.end());nodes.erase(std::unique(nodes.begin(),nodes.end()),nodes.end());
                std::fprintf(frontier,"T\t%zu\t%d\t%zu",size_t(net),int(_net_list.net_is_ignored(net)),nodes.size());
                for(auto n:nodes)std::fprintf(frontier,"\t%zu",n);
                std::fputc('\n',frontier);
            }
            if(std::ferror(frontier))throw std::runtime_error("RR frontier write");
        }
'''
 s=s.replace(anchor,code+anchor);f.write_text(s);compile=[x.replace(str(B)+'/',str(D)+'/') for x in p['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for q in (D/'source').rglob('*'):
  if q.is_file():bindings[str(q)]=sha(q)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='All RR node type/capacity/occupancy/history/base/single-present/cost-index, allNET full unique node support, NET2 bounding-box/global worst slack. Not full router internal state or topology. Runtime equivalence pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='FULL_RR_FRONTIER_OBSERVER_BUILT_RUNTIME_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('FULL_RR_FRONTIER_OBSERVER_BUILT')
if __name__=='__main__':main()
