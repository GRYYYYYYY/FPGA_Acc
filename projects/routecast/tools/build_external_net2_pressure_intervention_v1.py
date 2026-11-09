"""Private scoped CHANNEL pressure offsets around one native NET call."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
B=R/'build/native_external_early_net_observer_v1_2026-10-19';D=R/'build/native_external_net2_pressure_intervention_v1_2026-10-19'
def main():
 b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/overlay/SerialNetlistRouter.tpp';s=f.read_text();anchor='        NetResultFlags flags = route_net(';assert s.count(anchor)==1
 code=r'''
        struct PressureGuard {
            std::vector<std::pair<RRNodeId,int>> offsets;
            bool active=false;
            PressureGuard(ParentNetId net) {
                auto& ctx=g_vpr_ctx.mutable_routing();const auto& graph=g_vpr_ctx.device().rr_graph;
                std::vector<std::pair<RRNodeId,int>> desired;
                std::vector<size_t> own;
                if(ctx.route_trees[net])for(const auto& node:ctx.route_trees[net]->all_nodes())own.push_back(size_t(node.inode));
                std::sort(own.begin(),own.end());
                FILE* file=std::fopen("pressure.tsv","r");if(!file)throw std::runtime_error("pressure input absent");
                std::unique_ptr<FILE,decltype(&std::fclose)> guard(file,&std::fclose);
                for(auto id:graph.nodes()) {
                    auto type=graph.node_type(id);if(type!=CHANX && type!=CHANY)continue;
                    size_t n=0;int expected=-1,value=-1;
                    if(std::fscanf(file,"%zu%d%d",&n,&expected,&value)!=3 || n!=size_t(id) || expected<0 || value<0 || ctx.rr_node_route_inf[id].occ()!=expected)throw std::runtime_error("pressure domain/stale/nonnegative mismatch");
                    if(std::binary_search(own.begin(),own.end(),n) && value<1)throw std::runtime_error("pressure lacks own NET");
                    desired.emplace_back(id,value);if(expected!=value)offsets.emplace_back(id,expected-value);
                }
                int extra=0;if(std::fscanf(file,"%d",&extra)!=EOF)throw std::runtime_error("pressure trailing input");
                for(auto entry:desired)ctx.rr_node_route_inf[entry.first].set_occ(entry.second);
                active=true;VTR_LOG("RC_PRESSURE_APPLIED channels=%zu modified=%zu\n",desired.size(),offsets.size());
            }
            void restore() {
                if(!active)return;auto& ctx=g_vpr_ctx.mutable_routing();
                for(auto entry:offsets)if(ctx.rr_node_route_inf[entry.first].occ()+entry.second<0)throw std::runtime_error("pressure restore negative");
                for(auto entry:offsets)ctx.rr_node_route_inf[entry.first].set_occ(ctx.rr_node_route_inf[entry.first].occ()+entry.second);
                active=false;VTR_LOG("RC_PRESSURE_RESTORED modified=%zu\n",offsets.size());
            }
            ~PressureGuard() {if(active){try{restore();}catch(...){std::terminate();}}}
        };
        std::unique_ptr<PressureGuard> pressure;
        if(itry==2 && inet==1 && size_t(net_id)==2)pressure.reset(new PressureGuard(net_id));
'''
 s=s.replace(anchor,code+anchor);after="        observe('A',inet,net_id);";assert s.count(after)==1;s=s.replace(after,"        if(pressure)pressure->restore();\n"+after);f.write_text(s);compile=[x.replace(str(B)+'/',str(D)+'/') for x in p['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for q in (D/'source').rglob('*'):
  if q.is_file():bindings[str(q)]=sha(q)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Validate full CHANNEL target demand before mutation; save expected-minus-desired offsets, native NET2 then restore offsets with nonnegative prevalidation and exception guard. Only pressure changes; shadow diagnostic, not tree-consistent during call. Runtime equivalence/guard contracts pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='PRESSURE_INTERVENTION_BUILT_RUNTIME_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('PRESSURE_BINARY_BUILT')
if __name__=='__main__':main()
