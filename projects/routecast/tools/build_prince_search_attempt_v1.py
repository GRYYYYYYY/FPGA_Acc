"""Append-only observer and owned search-attempt scopes, original routing unchanged."""
import json,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_search_attempt_v1_2026-10-20';OLD=R/'build/prince_competitive_frontier_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);p=json.loads((OLD/'protocol.json').read_text());s=(OLD/'connection_router.cpp').read_text();marker=' // RCATT'
 declaration='''extern "C" void routecast_attempt_begin(RRNodeId,const t_conn_cost_params&,const t_bb&,const t_bb&,bool); // RCATT
extern "C" void routecast_attempt_found(RRNodeId,float,float,float); // RCATT
extern "C" void routecast_attempt_end(); // RCATT
extern "C" void routecast_attempt_unsupported(); // RCATT
struct RouteCastAttemptScope {RouteCastAttemptScope(RRNodeId sink,const t_conn_cost_params& c,const t_bb& b,const t_bb& target,bool rcv){routecast_attempt_begin(sink,c,b,target,rcv);}~RouteCastAttemptScope(){routecast_attempt_end();}}; // RCATT
'''
 needle='extern "C" void routecast_connection_end();';assert s.count(needle)==1;s=s.replace(needle,needle+'\n'+declaration)
 needle='    target_bb.layer_max = rr_graph_->node_layer(RRNodeId(sink_node));';assert s.count(needle)==1;s=s.replace(needle,needle+'\n    RouteCastAttemptScope routecast_attempt_scope(sink_node,cost_params,bounding_box,target_bb,rcv_path_manager.is_enabled());'+marker)
 needle='        if (inode == sink_node) {';assert s.count(needle)==1;s=s.replace(needle,needle+'\n            routecast_attempt_found(inode,new_total_cost,rr_node_route_inf_[inode].path_cost,rr_node_route_inf_[inode].backward_path_cost);'+marker)
 needle='    RouteCastConnectionScope routecast_scope(rt_root,RRNodeId::INVALID(),conn_params);';assert s.count(needle)==1;s=s.replace(needle,needle+'\n    routecast_attempt_unsupported();'+marker)
 cp=D/'connection_router.cpp';cp.write_text(s);stripped='\n'.join(line for line in s.splitlines() if '// RCATT' not in line);assert stripped.split()==(OLD/'connection_router.cpp').read_text().split()
 observer=(OLD/'observer.cpp').read_text();observer+='''
#include "connection_router_interface.h"
static thread_local std::array<uint64_t,32> attempt_record{};
static thread_local bool attempt_active=false,attempt_found=false;
static thread_local uint64_t attempt_serial=0,attempt_last_connection=0,attempt_ordinal=0;
static bool attempt_enabled(){return frontier_enabled()&&!frontier_closed;}
static std::ofstream& attempt_stream(){static std::ofstream f(std::string(std::getenv("ROUTECAST_FRONTIER_FILE"))+".attempts.bin",std::ios::binary);static bool header=false;if(!f)throw std::runtime_error("attempt file open");if(!header){f.write("RCATT001",8);header=true;}return f;}
static void attempt_emit(uint64_t tag){attempt_record[0]=tag;attempt_record[9]=frontier_sequence;attempt_record[31]=attempt_found;attempt_stream().write(reinterpret_cast<const char*>(attempt_record.data()),sizeof(attempt_record));if(!attempt_stream())throw std::runtime_error("attempt write");}
extern "C" void routecast_attempt_begin(RRNodeId sink,const t_conn_cost_params& cost,const t_bb& b,const t_bb& target,bool rcv){
 if(!attempt_enabled())return;
 if(attempt_active||!connection_active||!query_scope||query_net<0||size_t(sink)!=connection_sink)throw std::runtime_error("attempt begin context");
 attempt_active=true;attempt_found=false;if(attempt_last_connection!=connection_id){attempt_last_connection=connection_id;attempt_ordinal=0;}++attempt_ordinal;
 attempt_record={{1,uint64_t(phase_iteration+1),uint64_t(query_net),connection_id,connection_pin,connection_sink,++attempt_serial,attempt_ordinal,ledger_epoch,frontier_sequence,uint64_t(int64_t(b.xmin)),uint64_t(int64_t(b.xmax)),uint64_t(int64_t(b.ymin)),uint64_t(int64_t(b.ymax)),uint64_t(int64_t(b.layer_min)),uint64_t(int64_t(b.layer_max)),uint64_t(int64_t(target.xmin)),uint64_t(int64_t(target.xmax)),uint64_t(int64_t(target.ymin)),uint64_t(int64_t(target.ymax)),uint64_t(int64_t(target.layer_min)),uint64_t(int64_t(target.layer_max)),qbits(cost.criticality),qbits(cost.astar_fac),qbits(cost.astar_offset),qbits(cost.bend_cost),qbits(cost.pres_fac),uint64_t(rcv),0,0,0,0}};attempt_emit(1);
}
extern "C" void routecast_attempt_found(RRNodeId sink,float popped,float stored,float backward){
 if(!attempt_enabled())return;
 if(!attempt_active||attempt_found||size_t(sink)!=connection_sink||attempt_record[3]!=connection_id||attempt_record[8]!=ledger_epoch)throw std::runtime_error("attempt found context");
 attempt_found=true;attempt_record[28]=qbits(popped);attempt_record[29]=qbits(stored);attempt_record[30]=qbits(backward);attempt_emit(2);
}
extern "C" void routecast_attempt_end(){
 if(!attempt_enabled())return;
 if(!attempt_active||!connection_active||attempt_record[3]!=connection_id||attempt_record[8]!=ledger_epoch)throw std::runtime_error("attempt end context");
 attempt_emit(3);attempt_active=false;
}
extern "C" void routecast_attempt_unsupported(){
 if(!attempt_enabled())return;
 if(attempt_active||!connection_active)throw std::runtime_error("unsupported attempt context");
 attempt_record={};attempt_record[1]=phase_iteration+1;attempt_record[2]=query_net;attempt_record[3]=connection_id;attempt_record[4]=connection_pin;attempt_record[5]=connection_sink;attempt_record[8]=ledger_epoch;attempt_found=false;attempt_emit(9);
}
'''
 op=D/'observer.cpp';op.write_text(observer);assert observer.startswith((OLD/'observer.cpp').read_text());cc=p['connection_compile'].copy();cc[cc.index('-c')+1]=str(cp);cc[cc.index('-o')+1]=str(D/'connection_router.cpp.o');oc=p['compile'].copy();oc[oc.index('-c')+1]=str(op);oc[oc.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(OLD/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');archive=next(Path(x) for x in link if x.endswith('/libvpr.a'));owned=D/'libvpr.a';shutil.copyfile(archive,owned);link=[str(owned) if x==str(archive) else x for x in link];design=R/'experiments/prince_ready_NET_geometry_v2_2026-10-20/exact_search_attempt_observation_design_v1.json';bindings={str(x):sha(x) for x in [Path(__file__),OLD/'protocol.json',OLD/'receipt.json',OLD/'connection_router.cpp',OLD/'observer.cpp',cp,op,archive,design]};fields=['tag','phase','NET','connection','pin','sink','attempt_serial','connection_attempt_ordinal','ledger_epoch','frontier_sequence','xmin','xmax','ymin','ymax','layer_min','layer_max','target_xmin','target_xmax','target_ymin','target_ymax','target_layer_min','target_layer_max','criticality_bits','astar_fac_bits','astar_offset_bits','bend_cost_bits','pres_fac_bits','RCV','popped_sink_f_bits','stored_sink_f_bits','stored_sink_g_bits','found'];assert len(fields)==32
 (D/'protocol.json').write_text(json.dumps(dict(connection_compile=cc,compile=oc,link=link,bindings=bindings,schema=dict(magic='RCATT001',record='32 little-endian uint64 words; signed coordinates encoded int64',fields=fields,tags={'1':'begin','2':'native target pop','3':'end','9':'unsupported all-shortest-paths'},cutoff='Same actual ready cutoff as unchanged CHANNEL frontier;unsuccessful end has found0 and zero sentinel cost words.'),scope='Observer append-only;owned connection source tokens identical after removing RCATT lines. Existing CHANNEL frontier format/cost wrapper untouched;identity validation pending.'),indent=2)+'\n')
 for name,cmd in [('connection_compile',cc),('observer_compile',oc),('archive_replace',['ar','r',str(owned),str(D/'connection_router.cpp.o')]),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',owned,cp,op,D/'observer.o',D/'connection_router.cpp.o']}),indent=2)+'\n');(D/'source_invariance_v1.json').write_text(json.dumps(dict(connection_tokens_without_hooks_equal=True,observer_append_only=True,original_cost_wrapper_byte_identical=True),indent=2)+'\n')
if __name__=='__main__':main()
