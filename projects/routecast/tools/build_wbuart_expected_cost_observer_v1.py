"""Private connection-router observer preserves original MAP call/result exactly."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';B=R/'build/wbuart_corrected_utility_native_v1_2026-10-20';O=R/'build/native_excess_preload_state_v2_2026-10-19';D=R/'build/wbuart_expected_cost_observer_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 design=E/'wbuart_expected_cost_observer_design_v1_2026-10-20';design.mkdir(exist_ok=False);source=V/'vpr/src/route/connection_router.cpp';files=[Path(__file__),source,V/'vpr/src/route/router_lookahead_map.cpp',V/'vpr/src/route/router_lookahead.h',R/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp',B/'receipt.json'];bindings={str(p):sha(p) for p in files};(design/'protocol.json').write_text(json.dumps({'status':'FROZEN_SOURCE_ONLY_NATIVE_EXPECTED_COST_OBSERVER','selection':'Record NET ID0 at all source-layout routing calls, all pins; deterministic fixed NET before new observer results, no target-label selection.','fields':'stage(seed/expand),nativeNET/localPin,current/targetRR,float32 bits of criticality,pres_fac,R_upstream,expected_cost,backward_cost,actual priority,astar_fac,astar_offset.','semantics':'Observe actual original MAP get_expected_cost result after native priority expression; no second query, no altered branches, no clipped/changed paths. Current corrected native core/groupOR linkage retained.','qualification':'Observer-off and observer-on across all3 source widths; full physical/canonical/owner trace/source byte parity and work-counter equivalence; exact float32 priority reconstruction on emitted samples before any target capture or model heuristic use.','limits':'Samples carry NET/pin/node/target and dynamic factor but no complete occupancy/iteration query token; not a full replayable routing snapshot. No native expected-cost lower-bound/admissibility assertion and no full-model equivalence.','bindings':bindings},indent=2)+'\n');D.mkdir(exist_ok=False);(D/'source').mkdir();s=source.read_text();header=r'''
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <stdexcept>
static uint32_t routecast_expected_bits(float x){uint32_t v;std::memcpy(&v,&x,4);return v;}
static void routecast_expected_observe(const char* stage,size_t net,int pin,size_t node,size_t target,float criticality,float pres,float upstream,float expected,float backward,float priority,float astar,float offset){
 if(net!=0)return;
 const char* path=std::getenv("ROUTECAST_EXPECTED_COST_TRACE");if(!path)return;
 static FILE* file=nullptr;
 if(!file){file=std::fopen(path,"wx");if(!file)throw std::runtime_error("expected cost observer exclusive open failed");std::fprintf(file,"EXPECTED_COST 1\n");}
 std::fprintf(file,"Q %s %zu %d %zu %zu %08x %08x %08x %08x %08x %08x %08x %08x\n",stage,net,pin,node,target,routecast_expected_bits(criticality),routecast_expected_bits(pres),routecast_expected_bits(upstream),routecast_expected_bits(expected),routecast_expected_bits(backward),routecast_expected_bits(priority),routecast_expected_bits(astar),routecast_expected_bits(offset));
 if(std::ferror(file))throw std::runtime_error("expected cost observer write failed");
}
'''
 expand='        total_cost += to->backward_path_cost + cost_params.astar_fac * std::max(0.f, expected_cost - cost_params.astar_offset);';seed='        float tot_cost = backward_path_cost + cost_params.astar_fac * std::max(0.f, expected_cost - cost_params.astar_offset);';assert s.count(expand)==s.count(seed)==1
 eh='\n        routecast_expected_observe("expand",size_t(conn_params_->net_id_),conn_params_->target_pin_num_,size_t(to->index),size_t(target_node),cost_params.criticality,cost_params.pres_fac,to->R_upstream,expected_cost,to->backward_path_cost,total_cost,cost_params.astar_fac,cost_params.astar_offset);';sh='\n        routecast_expected_observe("seed",size_t(conn_params_->net_id_),conn_params_->target_pin_num_,size_t(inode),size_t(target_node),cost_params.criticality,cost_params.pres_fac,R_upstream,expected_cost,backward_path_cost,tot_cost,cost_params.astar_fac,cost_params.astar_offset);';s=header+s.replace(expand,expand+eh).replace(seed,seed+sh);assert s.replace(header,'',1).replace(eh,'').replace(sh,'')==source.read_text();dst=D/'source/connection_router.cpp';dst.write_text(s);proof=json.loads((B/'receipt.json').read_text());assert sha(proof['binary'])==proof['binary_sha256'] and all(sha(p)==h for p,h in proof['bindings'].items());compile=json.loads((O/'protocol.json').read_text())['compile'];compile[compile.index('-c')+1]=str(dst);compile[compile.index('-o')+1]=str(D/'connection_router.o');link=json.loads((B/'protocol.json').read_text())['link'];link=[str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in link];link.insert(1,str(D/'connection_router.o'));bindings.update({str(dst):sha(dst),str(design/'protocol.json'):sha(design/'protocol.json')})
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps({'compile':compile,'link':link,'bindings':bindings,'observer_removal_exact_source_parity':True,'scope':'Read-only fixedNET0 actual expected-cost/priority sample observer. Source qualification pending.'},indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps({'binary':str(D/'sequence_vpr'),'binary_sha256':sha(D/'sequence_vpr'),'bindings':{**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},'source_qualification_pending':True},indent=2)+'\n');print('EXPECTED_COST_OBSERVER_PRIVATE_BUILD_PASS')
if __name__=='__main__':main()
