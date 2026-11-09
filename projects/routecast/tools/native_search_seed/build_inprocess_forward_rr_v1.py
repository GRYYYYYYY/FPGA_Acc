"""Exact forward radix search using live RR getters, no copied dest/inc/cap CSR arrays."""
import json,sys,subprocess,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();D=R/'build/native_inprocess_forward_rr_v1_2026-10-10';assert not D.exists();D.mkdir();S=D/'source';S.mkdir();base=R/'build/native_candidate_retained_search_2026-10-06';inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());metadata=R/'experiments/native_switch_exact_rc_boundary_v1_2026-10-10/exact_switch_metadata.json';m=json.loads(metadata.read_text());costs=[x['integer_arc_increment'] for x in m['switches']];assert len(costs)==4 and m['certified_all_node_R_C_zero'];kernel=R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp';original=kernel.read_text();start=original.index('extern "C" int rc_tree_workspace(');body=original[start:];body=body.replace('rc_tree_workspace(','rc_tree_workspace_native(',1).replace('void* handle,U n,','void* handle,const RRGraphView& graph,U n,',1).replace('const U* dest,const U* inc,const U* cap,','const U* switch_cost,',1)
body=body.replace('U v=dest[e];if(v>=n)return -1;if(!cap[v])continue;','U local=e-row[u];U v=size_t(graph.edge_sink_node(RRNodeId(u),local));if(v>=n)return -1;if(!graph.node_capacity(RRNodeId(v)))continue;U edge_increment=switch_cost[graph.edge_switch(RRNodeId(u),local)];').replace('inc[e]','edge_increment');(S/'native_forward_kernel.h').write_text(original+'\n'+body)
hook=r'''    if(const char* manifest=std::getenv("ROUTECAST_INPROCESS_QUERIES")) {
        const char* output=std::getenv("ROUTECAST_INPROCESS_FLOORS");
        if(!output || is_flat)throw std::runtime_error("inprocess floor configuration invalid");
        const auto& rr=device_ctx.rr_graph;
        if(rr.num_nodes()!=91088 || rr.num_rr_switches()!=4)throw std::runtime_error("unsupported inprocess exact graph");
        std::vector<U> row(1,0),raw(rr.num_nodes()),pn(rr.num_nodes()),pe(rr.num_nodes()),price(rr.num_nodes(),0);
        std::vector<uint8_t> settled(rr.num_nodes());
        for(auto node:rr.nodes()) {if(rr.node_R(node)!=0 || rr.node_C(node)!=0)throw std::runtime_error("nonzero nodeRC");row.push_back(row.back()+rr.num_edges(node));}
        if(row.back()!=801735)throw std::runtime_error("unsupported inprocess edges");
        const U switch_cost[4]={COSTS};
        for(size_t sid=0;sid<4;++sid) {
            if(rr.rr_switch_inf(RRSwitchId(sid)).R!=0 || rr.rr_switch_inf(RRSwitchId(sid)).Tdel!=float(double(switch_cost[sid])/1e18))throw std::runtime_error("exact switch metadata mismatch");
        }
        struct Query {U cid,pin,source,sink;};
        std::ifstream input(manifest);if(!input)throw std::runtime_error("manifest open failed");
        std::map<U,std::pair<U,U>> netmeta;std::map<U,std::vector<Query>> queries;char kind;
        while(input>>kind) {
            U a,b,c,d,e;
            if(kind=='N') {if(!(input>>a>>b>>c) || !netmeta.emplace(a,std::make_pair(b,c)).second)throw std::runtime_error("invalid NET manifest");}
            else if(kind=='Q') {if(!(input>>a>>b>>c>>d>>e))throw std::runtime_error("invalid query manifest");queries[b].push_back({a,c,d,e});}
            else throw std::runtime_error("unknown manifest record");
        }
        size_t netcount=0;
        for(auto net:net_list.nets()) {const auto expected=netmeta.at(size_t(net));if(expected.first!=U(net_list.net_is_ignored(net)) || expected.second!=net_list.net_pins(net).size())throw std::runtime_error("live NET changed");++netcount;}
        if(netcount!=netmeta.size())throw std::runtime_error("NET scope mismatch");
        FILE* fp=std::fopen(output,"w");if(!fp)throw std::runtime_error("floor output open failed");
        Workspace workspace(rr.num_nodes());size_t completed=0;
        for(const auto& entry:queries) {
            auto net=ClusterNetId(entry.first);std::vector<U> targets;U source=entry.second.front().source;
            for(const auto& q:entry.second) {
                if(q.source!=source || q.pin>=route_ctx.net_rr_terminals[net].size() || size_t(route_ctx.net_rr_terminals[net][0])!=source || size_t(route_ctx.net_rr_terminals[net][q.pin])!=q.sink)throw std::runtime_error("live endpoint changed");
                targets.push_back(q.sink);
            }
            int status=rc_tree_workspace_native(&workspace,rr,rr.num_nodes(),source,0,0,targets.data(),targets.size(),row.data(),switch_cost,price.data(),raw.data(),pn.data(),pe.data(),settled.data());
            if(status)throw std::runtime_error("native forward search rejected");
            for(const auto& q:entry.second) {
                if(!settled[q.sink])throw std::runtime_error("required sink not settled");
                std::vector<U> path;U u=q.sink;
                while(u!=source) {if(pn[u]>=rr.num_nodes() || pe[u]>=row.back() || path.size()>=rr.num_nodes())throw std::runtime_error("invalid parent");path.push_back(pe[u]);u=pn[u];}
                std::reverse(path.begin(),path.end());std::fprintf(fp,"Q\t%llu\t%llu\t%zu",(unsigned long long)q.cid,(unsigned long long)raw[q.sink],path.size());
                for(U edge:path)std::fprintf(fp,"\t%llu",(unsigned long long)edge);std::fprintf(fp,"\n");++completed;
            }
        }
        bool failed=std::ferror(fp);int closed=std::fclose(fp);if(failed || closed || completed!=6273)throw std::runtime_error("incomplete native floors");
        VTR_LOG("ROUTECAST live RR forward floors complete=%zu without edge-array copies\n",completed);
    }
'''.replace('COSTS',','.join(str(c)+'ULL' for c in costs))
s=(base/'source/route.cpp').read_text();s='#include <fstream>\n#include <map>\n#include "native_forward_kernel.h"\n'+s;needle='    const bool retained_input=routecast_retained_pending;';assert s.count(needle)==1;s=s.replace(needle,hook+needle);(S/'route.cpp').write_text(s);(S/'build.py').write_text(Path(__file__).read_text());bindings={str(q):sha(q) for q in [Path(__file__).resolve(),metadata,kernel,base/'source/route.cpp']};b=json.loads((base/'receipt.json').read_text());bindings.update(b['shared_inputs_sha256']);assert all(sha(q)==h for q,h in bindings.items());cmd=[*p['compile'][:-4],'-c',str(S/'route.cpp'),'-o',str(D/'route.o')]
with (D/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(D/'route.o'),str(inputs/'sync_once.o'),wrap]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(q)==h for q,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),source_sha256={str(q):sha(q) for q in S.iterdir()},scope='Inprocess borrowed RR forward zero-price floor probe. Not hybrid singleton/feedback/fullpredictor or actual route change. Manifest acquisition and nodeprefix construction paid separately.'),indent=2)+'\n');print('INPROCESS FORWARD BUILT')
