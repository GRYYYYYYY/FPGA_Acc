"""Graph-bound fixedNET0 native const MAP endpoints; private route object only."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=R/'build/native_excess_preload_state_v2_2026-10-19';B=R/'build/wbuart_expected_cost_observer_v1_2026-10-20';D=R/'build/wbuart_map_query_probe_v3_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);(D/'source').mkdir();design=E/'wbuart_map_query_probe_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in json.loads(design.read_text())['bindings'].items());br=json.loads((B/'receipt.json').read_text());assert sha(br['binary'])==br['binary_sha256'] and all(sha(p)==h for p,h in br['bindings'].items());src=O/'source/route.cpp';s=src.read_text();headers='#include "connection_router_interface.h"\n#include <cstdio>\n#include <cstring>\n#include <cstdint>\n';needle='    VTR_ASSERT(router_lookahead != nullptr);';assert s.count(needle)==1
 hook=r'''
    const char* routecast_probe_path=std::getenv("ROUTECAST_MAP_QUERY_PROBE");
    if(routecast_probe_path) {
        const char* graph_hash=std::getenv("ROUTECAST_MAP_PROBE_GRAPH_SHA256");
        const char* endpoint_hash=std::getenv("ROUTECAST_MAP_PROBE_ENDPOINT_SHA256");
        if(is_flat || !graph_hash || !endpoint_hash || std::strlen(graph_hash)!=64 || std::strlen(endpoint_hash)!=64)
            throw std::runtime_error("MAP probe requires clustered bound graph and endpoint hashes");
        ParentNetId net{0};
        if(net_list.net_is_ignored(net) || net_list.net_sinks(net).size()!=2)
            throw std::runtime_error("MAP probe fixedNET0 two-pin domain");
        const auto& rr=device_ctx.rr_graph;
        RRNodeId source=route_ctx.net_rr_terminals[net][0];
        std::vector<unsigned char> allowed(rr.num_nodes(),0);
        for(auto node:rr.nodes()) {
            auto kind=rr.node_type(node);
            if(kind==CHANX || kind==CHANY || kind==IPIN || kind==SINK)allowed[size_t(node)]=1;
            for(auto edge:rr.edges(node)) {
                auto sink=rr.edge_sink_node(node,edge);
                if(rr.node_type(sink)==SOURCE || (rr.node_type(sink)==OPIN && kind!=SOURCE))
                    throw std::runtime_error("MAP probe unsupported SOURCE/OPIN graph grammar");
            }
        }
        allowed[size_t(source)]=1;
        for(auto edge:rr.edges(source)) {
            auto node=rr.edge_sink_node(source,edge);
            if(rr.node_type(node)!=OPIN)throw std::runtime_error("MAP probe source exit not OPIN");
            allowed[size_t(node)]=1;
        }
        size_t domain=0;for(auto flag:allowed)domain+=bool(flag);
        FILE* file=std::fopen(routecast_probe_path,"wx");
        if(!file)throw std::runtime_error("MAP probe exclusive open failed");
        auto bits=[](float x){uint32_t word;std::memcpy(&word,&x,4);return word;};
        std::fprintf(file,"MAP_QUERY 1 %s %s %zu %zu %zu\n",graph_hash,endpoint_hash,rr.num_nodes(),domain,size_t(source));
        for(int pin=1;pin<=2;++pin) {
            RRNodeId target=route_ctx.net_rr_terminals[net][pin];
            std::fprintf(file,"T %d %zu\n",pin,size_t(target));
            t_conn_cost_params params;
            params.astar_fac=router_opts.astar_fac;params.astar_offset=router_opts.astar_offset;
            params.bend_cost=router_opts.bend_cost;params.pres_fac=router_opts.first_iter_pres_fac;
            for(auto node:rr.nodes())if(allowed[size_t(node)]) {
                params.criticality=0.f;float zero=router_lookahead->get_expected_cost(node,target,params,0.f);
                params.criticality=1.f;float one=router_lookahead->get_expected_cost(node,target,params,0.f);
                std::fprintf(file,"Q %d %zu %zu %08x %08x\n",pin,size_t(node),size_t(target),bits(zero),bits(one));
            }
        }
        bool failed=std::ferror(file);if(std::fclose(file) || failed)throw std::runtime_error("MAP probe write failed");
        VTR_LOG("ROUTECAST_MAP_QUERY_PROBE nodes=%zu domain=%zu targets=2\n",rr.num_nodes(),domain);
    }
'''
 s=headers+s.replace(needle,needle+hook);assert s.replace(headers,'',1).replace(hook,'')==src.read_text();dst=D/'source/route.cpp';dst.write_text(s)
 for p in (O/'source').glob('*.h'):shutil.copyfile(p,D/'source'/p.name)
 compile=json.loads((O/'protocol.json').read_text())['compile'];compile[compile.index('-c')+1]=str(dst);compile[compile.index('-o')+1]=str(D/'route.o');link=json.loads((B/'protocol.json').read_text())['link'];link=[str(D/'route.o') if x==str(O/'route.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in link];assert str(D/'route.o') in link;bindings={str(p):sha(p) for p in [Path(__file__),design,B/'receipt.json',B/'protocol.json',src,dst,*list((D/'source').glob('*.h'))]}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps({'compile':compile,'link':link,'bindings':bindings,'hook_removal_recovers_original_route_source':True,'scope':'Original const MAP API query fixture at0/1, NET0 two targets, graph grammar restricted. Native routing/sample parity pending; no model change.'},indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps({'binary':str(D/'sequence_vpr'),'binary_sha256':sha(D/'sequence_vpr'),'bindings':{**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},'qualification_pending':True},indent=2)+'\n');print('BOUNDED_MAP_QUERY_PROBE_BUILD_PASS')
if __name__=='__main__':main()
