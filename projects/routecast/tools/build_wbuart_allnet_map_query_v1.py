"""Private all-target dense native MAP query exporter; vendor remains read-only."""
import ast,json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=R/'build/native_excess_preload_state_v2_2026-10-19';B=R/'build/wbuart_expected_cost_observer_v1_2026-10-20';D=R/'build/wbuart_allnet_map_query_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);(D/'source').mkdir();design=E/'wbuart_allnet_map_query_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in json.loads(design.read_text())['bindings'].items());br=json.loads((B/'receipt.json').read_text());assert sha(br['binary'])==br['binary_sha256'];src=O/'source/route.cpp';s=src.read_text();headers='#include "connection_router_interface.h"\n#include <cstdio>\n#include <cstring>\n#include <cstdint>\n#include <set>\n#include <chrono>\n';needle='    VTR_ASSERT(router_lookahead != nullptr);';assert s.count(needle)==1
 hook=r'''
    const char* rc_allmap_path=std::getenv("ROUTECAST_ALLNET_MAP_QUERY");
    if(rc_allmap_path) {
        auto started=std::chrono::steady_clock::now();
        const char* gh=std::getenv("ROUTECAST_MAP_PROBE_GRAPH_SHA256");
        const char* eh=std::getenv("ROUTECAST_MAP_PROBE_ENDPOINT_SHA256");
        if(is_flat || !gh || !eh || std::strlen(gh)!=64 || std::strlen(eh)!=64)
            throw std::runtime_error("allMAP clustered graph/frame binding required");
        const auto& rr=device_ctx.rr_graph;
        for(auto node:rr.nodes())for(auto edge:rr.edges(node)) {
            auto v=rr.edge_sink_node(node,edge);
            if(rr.node_type(v)==SOURCE || (rr.node_type(v)==OPIN && rr.node_type(node)!=SOURCE))
                throw std::runtime_error("allMAP unsupported SOURCE/OPIN grammar");
        }
        std::set<size_t> targets;
        size_t pins=0;
        for(auto net:net_list.nets())if(!net_list.net_is_ignored(net)) {
            for(size_t pin=1;pin<=net_list.net_sinks(net).size();++pin) {
                auto target=route_ctx.net_rr_terminals[net][pin];
                if(rr.node_type(target)!=SINK)throw std::runtime_error("allMAP nonSINK target");
                targets.insert(size_t(target));++pins;
            }
        }
        FILE* f=std::fopen(rc_allmap_path,"wx");if(!f)throw std::runtime_error("allMAP exclusive open");
        std::fprintf(f,"ALLMAP 1 %s %s %zu %zu %zu\n",gh,eh,rr.num_nodes(),targets.size(),pins);
        for(auto net:net_list.nets())if(!net_list.net_is_ignored(net))
            for(size_t pin=1;pin<=net_list.net_sinks(net).size();++pin)
                std::fprintf(f,"P %zu %zu %zu %zu\n",size_t(net),pin,size_t(route_ctx.net_rr_terminals[net][0]),size_t(route_ctx.net_rr_terminals[net][pin]));
        for(auto target:targets)std::fprintf(f,"T %zu\n",target);
        std::fprintf(f,"DATA\n");
        auto bits=[](float x){uint32_t w;std::memcpy(&w,&x,4);return w;};
        std::vector<unsigned char> block(size_t(rr.num_nodes())*8);
        t_conn_cost_params params;params.astar_fac=router_opts.astar_fac;params.astar_offset=router_opts.astar_offset;params.bend_cost=router_opts.bend_cost;params.pres_fac=router_opts.first_iter_pres_fac;
        for(auto target:targets) {
            for(auto node:rr.nodes())for(unsigned k=0;k<2;++k) {
                params.criticality=float(k);uint32_t w=bits(router_lookahead->get_expected_cost(node,RRNodeId(target),params,0.f));
                for(unsigned b=0;b<4;++b)block[size_t(node)*8+k*4+b]=(w>>(b*8))&255;
            }
            if(std::fwrite(block.data(),1,block.size(),f)!=block.size())throw std::runtime_error("allMAP payload write");
        }
        bool failed=std::ferror(f);if(std::fclose(f)||failed)throw std::runtime_error("allMAP close");
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();
        VTR_LOG("ROUTECAST_ALLMAP targets=%zu nodes=%zu pins=%zu seconds=%.9f\n",targets.size(),rr.num_nodes(),pins,seconds);
    }
'''
 s=headers+s.replace(needle,needle+hook);assert s.replace(headers,'',1).replace(hook,'')==src.read_text();dst=D/'source/route.cpp';dst.write_text(s)
 for p in (O/'source').glob('*.h'):shutil.copyfile(p,D/'source'/p.name)
 compile=json.loads((O/'protocol.json').read_text())['compile'];compile[compile.index('-c')+1]=str(dst);compile[compile.index('-o')+1]=str(D/'route.o');link=json.loads((B/'protocol.json').read_text())['link'];link=[str(D/'route.o') if x==str(O/'route.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in link];assert str(D/'route.o') in link;bindings={str(p):sha(p) for p in [Path(__file__),design,B/'receipt.json',B/'protocol.json',src,dst,*list((D/'source').glob('*.h'))]}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps({'compile':compile,'link':link,'bindings':bindings,'hook_removal_recovers_original':True,'qualification_pending':True},indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:
   result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  if result.returncode:
   (D/'failure.json').write_text(json.dumps({'stage':name,'exit_status':result.returncode})+'\n');raise RuntimeError(name+' failed')
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps({'binary':str(D/'sequence_vpr'),'binary_sha256':sha(D/'sequence_vpr'),'bindings':{**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},'qualification_pending':True},indent=2)+'\n');print('ALLNET_MAP_EXPORTER_BUILD_PASS')
if __name__=='__main__':main()
