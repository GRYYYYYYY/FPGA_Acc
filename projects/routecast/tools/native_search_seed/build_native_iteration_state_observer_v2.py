"""Only log original criticality return values; iteration stamp injected in independent route.cpp copy."""
import json,subprocess,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();B=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';D=R/'build/native_iteration_state_observer_v2_2026-10-10';D.mkdir();b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['source_sha256'].items())
inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';nm=subprocess.check_output(['nm',str(inputs/'libvpr.a')],text=True);symbols=[line.split()[-1] for line in nm.splitlines() if ' T _Z23get_net_pin_criticality' in line];assert len(symbols)==1;symbol=symbols[0]
route=(B/'source/route.cpp').read_text()
needle='        RouteIterResults iter_results = netlist_router->route_netlist(itry, pres_fac, worst_negative_slack);'
assert route.count(needle)==1
hook='''        if(std::getenv("ROUTECAST_CRITICALITY_TRACE")) {
            char iteration[32], factor[64];
            std::snprintf(iteration,sizeof(iteration),"%d",itry);
            std::snprintf(factor,sizeof(factor),"%.9g",double(pres_fac));
            if(::setenv("ROUTECAST_TRACE_ITERATION",iteration,1) || ::setenv("ROUTECAST_TRACE_PRES",factor,1))throw std::runtime_error("iteration telemetry env");
        }
'''
route=route.replace(needle,hook+needle)
state_needle='        wirelength_info = calculate_wirelength_info(net_list, available_wirelength);'
assert route.count(state_needle)==1
state_hook='        if(const char* directory=std::getenv("ROUTECAST_ITERATION_STATE_DIR")) {\n            std::string path=std::string(directory)+"/round_"+std::to_string(itry)+".tsv";\n            FILE* state=std::fopen(path.c_str(),"w");if(!state)throw std::runtime_error("iteration state open");\n            const auto& rc=g_vpr_ctx.routing();const auto& rr=g_vpr_ctx.device().rr_graph;\n            std::fprintf(state,"H\\t%d\\t%.9g\\t%.9g\\n",itry,double(pres_fac),double(itry==1 ? 0. : router_opts.acc_fac));\n            for(auto id:rr.nodes())std::fprintf(state,"N\\t%zu\\t%d\\t%d\\t%.9g\\n",size_t(id),int(rc.rr_node_route_inf[id].occ()),int(rr.node_capacity(id)),double(rc.rr_node_route_inf[id].acc_cost));\n            for(auto net:net_list.nets())if(rc.route_trees[net]) {\n                for(const auto& node:rc.route_trees[net]->all_nodes()) {\n                    auto parent=node.parent();\n                    std::fprintf(state,"T\\t%zu\\t%zu\\t%lld\\t%zu\\t%.9g\\t%d\\n",size_t(net),size_t(node.inode),parent ? static_cast<long long>(size_t(parent->inode)) : -1LL,size_t(node.parent_switch),double(node.Tdel),int(node.net_pin_index));\n                }\n            }\n            bool failed=std::ferror(state);int closed=std::fclose(state);if(failed || closed)throw std::runtime_error("iteration state write");\n        }\n'
route=route.replace(state_needle,state_hook+state_needle)
(D/'route.cpp').write_text(route)
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
with (D/'route_compile.log').open('w') as log:subprocess.run([*p['compile'][:-4],'-I'+str(B/'source'),'-c',str(D/'route.cpp'),'-o',str(D/'route.o')],stdout=log,stderr=subprocess.STDOUT,check=True)
source='''#include "globals.h"
#include "route_net.h"
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
extern "C" float REAL(const SetupHoldTimingInfo*,const ClusteredPinAtomPinsLookup&,float,float,ParentNetId,ParentPinId,bool);
struct Writer {
 FILE* fp=nullptr;unsigned long long sequence=0;
 Writer(){if(const char* p=std::getenv("ROUTECAST_CRITICALITY_TRACE")){fp=std::fopen(p,"w");if(!fp)throw std::runtime_error("criticality trace open");}}
 ~Writer(){if(fp){bool failed=std::ferror(fp);int code=std::fclose(fp);if(failed || code)std::abort();}}
};
extern "C" float WRAP(const SetupHoldTimingInfo* timing,const ClusteredPinAtomPinsLookup& lookup,float maximum,float exponent,ParentNetId net,ParentPinId pin,bool flat){
 float result=REAL(timing,lookup,maximum,exponent,net,pin,flat);
 static Writer writer;
 if(writer.fp){
  if(flat)throw std::runtime_error("criticality trace requires clustered mode");
  const auto& list=g_vpr_ctx.clustering().clb_nlist;ClusterPinId id{size_t(pin)};
  if(size_t(list.pin_net(id))!=size_t(net))throw std::runtime_error("criticality pin NET mismatch");
  std::fprintf(writer.fp,"C\\t%llu\\t%zu\\t%zu\\t%d\\t%.9g\\t%.9g\\t%.9g\\n",++writer.sequence,size_t(net),size_t(pin),list.pin_net_index(id),double(result),double(maximum),double(exponent));
  std::fprintf(writer.fp,"I\\t%llu\\t%s\\t%s\\n",writer.sequence,std::getenv("ROUTECAST_TRACE_ITERATION")?std::getenv("ROUTECAST_TRACE_ITERATION"):"0",std::getenv("ROUTECAST_TRACE_PRES")?std::getenv("ROUTECAST_TRACE_PRES"):"NA");
 }
 return result;
}
'''.replace('REAL','__real_'+symbol).replace('WRAP','__wrap_'+symbol)
(D/'observer.cpp').write_text(source)
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());compile=[*p['compile'][:-4],'-c',str(D/'observer.cpp'),'-o',str(D/'observer.o')]
with (D/'compile.log').open('w') as log:subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,check=True)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(D/'route.o'),str(inputs/'sync_once.o'),str(D/'observer.o'),wrap,'-Wl,--wrap='+symbol]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[Path(__file__),B/'receipt.json',B/'route.o',inputs/'libvpr.a',D/'observer.cpp',D/'observer.o',D/'route.cpp',D/'route.o']
bindings={**b['bindings'],**b['source_sha256'],**{str(p.resolve()):sha(p) for p in files}}
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),symbol=symbol,compile=compile,link=link,scope='Original criticality function called once per wrapper invocation; original float returned unchanged. Runtime call coverage/output identity unproven until trial.'),indent=2)+'\n');print('CRITICALITY OBSERVER BUILD PASS')
