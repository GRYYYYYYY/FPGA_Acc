"""Isolated opt-in PathFinder initial acc-cost preload; no routing-loop changes."""
import pathlib,json,hashlib,shutil,subprocess
R=pathlib.Path(__file__).resolve().parents[2]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
B=R/'build/native_owner_trace_cold_v1_2026-10-19';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and b['read_only_hooks_original_routing_source_recovered_exactly']
for p,h in b['bindings'].items():assert sha(p)==h,p
D=R/'build/native_excess_preload_v1_2026-10-19';D.mkdir();S=D/'source';S.mkdir();header=R/'tools/native_search_seed/excess_preload_v1_2026_10_19/routecast_excess_reader.h';shutil.copyfile(header,S/header.name)
original=(B/'source/route.cpp').read_text();text=original.replace('#include "routecast_owner_trace.h"','#include "routecast_owner_trace.h"\n#include "routecast_excess_reader.h"');anchor='    routecast_trace_begin(net_list);';assert text.count(anchor)==1
hook='''    if(const char* preload=std::getenv("ROUTECAST_EXCESS_PRELOAD")) {
        if(!*preload || is_flat || retained_input || (routecast_seed && *routecast_seed) || router_opts.initial_timing!=e_router_initial_timing::LOOKAHEAD || router_opts.router_algorithm!=e_router_algorithm::TIMING_DRIVEN)
            throw std::runtime_error("excess preload requires cold clustered LOOKAHEAD timing routing");
        const char* digest=std::getenv("ROUTECAST_EXCESS_GRAPH_SHA256");
        if(!digest)throw std::runtime_error("excess graph SHA contract missing");
        auto entries=rc_read_excess(preload,digest,device_ctx.rr_graph.num_nodes());
        if(!std::isfinite(router_opts.acc_fac)||router_opts.acc_fac<0)throw std::runtime_error("invalid native acc_fac");
        std::vector<std::pair<RRNodeId,float>> updates;updates.reserve(entries.size());size_t changed=0;
        for(const auto& entry:entries) {
            RRNodeId node(entry.node);auto kind=device_ctx.rr_graph.node_type(node);
            if((kind!=CHANX&&kind!=CHANY)||device_ctx.rr_graph.node_capacity(node)<=0||route_ctx.rr_node_route_inf[node].acc_cost!=1.f)
                throw std::runtime_error("excess preload node/domain/initial cost mismatch");
            float value=1.f+router_opts.acc_fac*entry.excess;
            if(!std::isfinite(value)||value<1.f)throw std::runtime_error("excess preloaded cost invalid");
            updates.emplace_back(node,value);if(value!=1.f)++changed;
        }
        for(const auto& update:updates)route_ctx.rr_node_route_inf[update.first].acc_cost=update.second;
        VTR_LOG("ROUTECAST initial excess preload entries=%zu changed=%zu acc_fac=%.9g\\n",entries.size(),changed,double(router_opts.acc_fac));
    }
'''
text=text.replace(anchor,hook+anchor);assert text.replace(hook,'').replace('#include "routecast_owner_trace.h"\n#include "routecast_excess_reader.h"','#include "routecast_owner_trace.h"')==original
(S/'route.cpp').write_text(text)
for name in ['routecast_owner_trace.h','routecast_owner_trace_impl.h']:shutil.copyfile(B/'source'/name,S/name)
shutil.copyfile(__file__,S/'build.py');P=json.loads((B/'protocol.json').read_text());compile=[*P['compile'][0][:-4],'-c',str(S/'route.cpp'),'-o',str(D/'route.o')];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in P['link']];bindings={**b['bindings'],str(bp):sha(bp),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(header):sha(header),str(pathlib.Path(__file__).resolve()):sha(__file__)}
for p in S.iterdir():bindings[str(p)]=sha(p)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,link=link,base_binary_sha256=b['binary_sha256'],hook_removal_recovers_original_source_exactly=True,scope='Opt-in initial acc-cost only; no loop/criticality/net order/seed changes. Caller must hash actual RR graph and provide matching SHA before native launch. Zero/default runtime equivalence mandatory; nonzero utility unproven.'),indent=2)+'\n')
print('EXCESS PRELOAD COMPILE',flush=True)
with (D/'compile.log').open('x') as f:subprocess.run(compile,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
with (D/'link.log').open('x') as f:subprocess.run(link,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),hook_removal_recovers_original_source_exactly=True,zero_and_absent_runtime_equivalence_pending=True,nonzero_native_jobs_launched=0),indent=2)+'\n');print('EXCESS PRELOAD BUILD PASS',flush=True)
