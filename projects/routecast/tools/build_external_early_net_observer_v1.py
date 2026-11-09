"""Private first3-round perNET before/after observer; unchanged route calls."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
B=R/'build/native_external_iteration_support_observer_v1_2026-10-19';D=R/'build/native_external_early_net_observer_v1_2026-10-19'
def main():
 b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/overlay/SerialNetlistRouter.tpp';s=f.read_text();anchor='    for (size_t inet = 0; inet < sorted_nets.size(); inet++) {';assert s.count(anchor)==1
 code=r'''
    FILE* raw_obs=itry<=3?std::fopen("early_net_trace.tsv",itry==1?"wx":"a"):nullptr;
    if(itry<=3 && !raw_obs)throw std::runtime_error("early NET observer open");
    std::unique_ptr<FILE,decltype(&std::fclose)> obs_guard(raw_obs,&std::fclose);
    auto observe=[&](char phase,size_t order,ParentNetId net) {
        if(!raw_obs || _net_list.net_is_ignored(net))return;
        std::vector<size_t> nodes;
        const auto& graph=g_vpr_ctx.device().rr_graph;
        if(route_ctx.route_trees[net])for(const auto& node:route_ctx.route_trees[net]->all_nodes()) {
            auto type=graph.node_type(node.inode);
            if(type==CHANX || type==CHANY)nodes.push_back(size_t(node.inode));
        }
        std::sort(nodes.begin(),nodes.end());nodes.erase(std::unique(nodes.begin(),nodes.end()),nodes.end());
        std::fprintf(raw_obs,"%c\t%d\t%zu\t%zu\t%.9g\t%zu",phase,itry,order,size_t(net),double(pres_fac),nodes.size());
        for(auto n:nodes) {
            auto id=RRNodeId(n);
            std::fprintf(raw_obs,"\t%zu:%d:%.9g:%.9g",n,route_ctx.rr_node_route_inf[id].occ(),double(route_ctx.rr_node_route_inf[id].acc_cost),double(get_single_rr_cong_pres_cost(id,pres_fac)));
        }
        std::fputc('\n',raw_obs);
        if(phase=='B')for(size_t pin=1;pin<_net_list.net_pins(net).size();++pin) {
            auto pid=_net_list.net_pin(net,pin);
            float crit=calculate_clb_net_pin_criticality(*_timing_info,_netlist_pin_lookup,pid,_is_flat);
            std::fprintf(raw_obs,"C\t%d\t%zu\t%zu\t%zu\t%.9g\t%.9g\n",itry,order,size_t(net),pin,double(_net_delay[net][pin]),double(crit));
        }
        if(std::ferror(raw_obs))throw std::runtime_error("early NET observer write");
    };
'''
 s=s.replace(anchor,code+anchor);before='        NetResultFlags flags = route_net(';assert s.count(before)==1;s=s.replace(before,"        observe('B',inet,net_id);\n"+before);after='            route_ctx.route_bb[net_id]);';assert s.count(after)==1;s=s.replace(after,after+"\n        observe('A',inet,net_id);");f.write_text(s)
 compile=[x.replace(str(B)+'/',str(D)+'/') for x in p['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for q in (D/'source').rglob('*'):
  if q.is_file():bindings[str(q)]=sha(q)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='First3 rounds actual perNET before/after old/current support CHANNEL occupancy, acc cost, single-resource present multiplier and pre-call setup-criticality/net_delay. Not full nonconfigurable group cost or sink internal scheduling. Runtime equivalence pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='EARLY_NET_OBSERVER_BUILT_EQUIVALENCE_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('EARLY_NET_OBSERVER_BUILT')
if __name__=='__main__':main()
