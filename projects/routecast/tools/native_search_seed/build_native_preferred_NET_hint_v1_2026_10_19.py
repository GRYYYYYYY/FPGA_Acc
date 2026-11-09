"""Isolated native NET-scoped first-iteration forecast hint; runtime unproven."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 B=R/'build/native_first_hint_connection_work_v1_2026-10-19';D=R/'build/native_preferred_NET_hint_v1_2026-10-19';D.mkdir(exist_ok=False);P=json.loads((B/'protocol.json').read_text());receipt=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==receipt['binary_sha256']
 shutil.copytree(B/'source',D/'source');src=D/'source';bindings={str(B/'protocol.json'):sha(B/'protocol.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for origin,name in [('tools/net_conditioned_native_adapter_v1/native_preferred_hint.h','native_preferred_hint.h'),('tools/net_conditioned_checked_import_v1/checked_claim_import.h','routecast_preferred_checked_import.h'),('tools/net_conditioned_hint_contract_v2/query_cost_frame.h','routecast_preferred_query_frame.h')]:
  p=R/origin;bindings[str(p)]=sha(p);(src/name).write_text(p.read_text().replace('../net_conditioned_hint_contract_v2/query_cost_frame.h','routecast_preferred_query_frame.h'))
 edits=[]
 def edit(p,a,z):
  s=p.read_text();assert s.count(a)==1,(str(p),a);p.write_text(s.replace(a,z));edits.append({'file':str(p),'old':a,'new':z})
 route=src/'route.cpp';edit(route,'#include "globals.h"','#include "globals.h"\n#include "native_preferred_hint.h"')
 edit(route,'    const bool retained_input=routecast_retained_pending;','''    struct RCPreferredLifecycle {
        ~RCPreferredLifecycle() noexcept {try {routecast_native_preferred_v1::finish();}catch(...) {std::terminate();}}
    } rc_preferred_lifecycle;
    if(std::getenv("ROUTECAST_PREFERRED_NET_CLAIMS") &&
       (!std::getenv("ROUTECAST_EXCESS_PRELOAD") || !std::getenv("ROUTECAST_FIRST_ITERATION_HINT") ||
        router_opts.acc_fac!=1.f || is_flat || routecast_retained_pending ||
        router_opts.router_algorithm!=e_router_algorithm::TIMING_DRIVEN))
        throw std::runtime_error("preferred hints require cold clustered serial TIMING_DRIVEN acc_fac1 and expiry preload");
    const bool retained_input=routecast_retained_pending;''')
 edit(route,'        for(const auto& update:updates)route_ctx.rr_node_route_inf[update.first].acc_cost=update.second;','        routecast_native_preferred_v1::initialize(net_list,digest,updates);\n        for(const auto& update:updates)route_ctx.rr_node_route_inf[update.first].acc_cost=update.second;')
 edit(route,'        if(rc_expire_first_hint && itry==1) {','        if(routecast_native_preferred_v1::frame && routecast_native_preferred_v1::frame->active())throw std::runtime_error("preferred query still active at iteration boundary");\n        if(rc_expire_first_hint && itry==1) {')
 edit(route,'    routecast_trace_finish(net_list,success);','    if(routecast_native_preferred_v1::frame)VTR_LOG("ROUTECAST preferred NET query scopes=%zu\\n",size_t(routecast_native_preferred_v1::query_count));\n    routecast_trace_finish(net_list,success);')
 tpp=src/'overlay/route_net.tpp';edit(tpp,'#include "routecast_owner_trace.h"','#include "routecast_owner_trace.h"\n#include "native_preferred_hint.h"')
 edit(tpp,'    // track time spent vs fanout','    routecast_native_preferred_v1::Scope rc_preferred_query(uint32_t(size_t(net_id)),itry);\n\n    // track time spent vs fanout')
 for p in src.rglob('*'):
  if p.is_file():bindings[str(p)]=sha(p)
 commands=[[x.replace(str(B)+'/',str(D)+'/') for x in c] for c in P['compile']];link=[x.replace(str(B)+'/',str(D)+'/') for x in P['link']]
 (D/'protocol.json').write_text(json.dumps({'bindings':bindings,'compile':commands,'link':link,'edits':edits,'scope':'Build only; disabled/zero parity, import rejection, runtime scope and utility all pending'},indent=2)+'\n')
 for i,c in enumerate(commands):
  print('PREFERRED COMPILE',i,flush=True)
  with (D/f'compile_{i}.log').open('x') as f:subprocess.run(c,stdout=f,stderr=subprocess.STDOUT,check=True,cwd=R)
 print('PREFERRED LINK',flush=True)
 with (D/'link.log').open('x') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True,cwd=R)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'receipt.json').write_text(json.dumps({'status':'PRIVATE_NATIVE_PREFERRED_HINT_BUILD_PASS_RUNTIME_PENDING','binary_sha256':sha(D/'sequence_vpr'),'protocol_sha256':sha(D/'protocol.json')},indent=2)+'\n');print('PREFERRED BUILD PASS',flush=True)
if __name__=='__main__':main()
