// Observation only after original print_route returns; no stop or native mutation.
#include "vpr_context.h"
#include "globals.h"
#include "route_utils.h"
#include "prince_live_view_v1.h"
#include <fstream>
#include <chrono>
#include <cstring>
#include <cstdlib>
#include <cstdio>
#include <cstdint>
#include <stdexcept>
#include <cmath>
#include <algorithm>
static int phase_iteration=0;static float phase_pres=0;static uint64_t phase_overused=0,phase_total=0,phase_worst=0;static int phase_updated=0;static float phase_timing[4]={};
static void consume_boundary(int);
extern "C" void SREAL(int,double,float,int,const RouterStats&,const OveruseInfo&,const WirelengthInfo&,std::shared_ptr<const SetupHoldTimingInfo>,float);
extern "C" void SWRAP(int i,double elapsed,float pres,int updated,const RouterStats& stats,const OveruseInfo& over,const WirelengthInfo& wire,std::shared_ptr<const SetupHoldTimingInfo> timing,float estimate){
 SREAL(i,elapsed,pres,updated,stats,over,wire,timing,estimate);
 phase_iteration=i;phase_pres=pres;phase_overused=over.overused_nodes;phase_total=over.total_overuse;phase_worst=over.worst_overuse;phase_updated=updated;
 if(!timing)throw std::runtime_error("missing timing context");
 phase_timing[0]=timing->setup_total_negative_slack();phase_timing[1]=timing->setup_worst_negative_slack();phase_timing[2]=timing->hold_total_negative_slack();phase_timing[3]=timing->hold_worst_negative_slack();
 consume_boundary(i);
}
extern "C" void REAL(const Netlist<>&,const char*,const char*,bool);
static uint64_t stamp(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
template<class T> static void put(std::ofstream& f,T x){f.write(reinterpret_cast<const char*>(&x),sizeof(x));}
static void capture_boundary(int iteration){
 auto begin=stamp();auto printed=begin;const char* directory=std::getenv("ROUTECAST_RESIDENT_BOUNDARY_DIR");if(!directory)return;
 if(phase_iteration!=iteration)throw std::runtime_error("boundary phase iteration mismatch");
 const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();
 std::string path=std::string(directory)+"/iteration_"+std::to_string(iteration)+".bin";std::ofstream f(path,std::ios::binary);if(!f)throw std::runtime_error("boundary output open");
 f.write("RCBND001",8);put<uint64_t>(f,iteration);put<uint64_t>(f,device.rr_graph.num_nodes());
 for(auto node:device.rr_graph.nodes()){
  uint32_t bits;float value=routing.rr_node_route_inf[node].acc_cost;std::memcpy(&bits,&value,4);
  put<uint64_t>(f,size_t(node));put<uint32_t>(f,uint32_t(device.rr_graph.node_type(node)));put<int32_t>(f,routing.rr_node_route_inf[node].occ());put<int32_t>(f,device.rr_graph.node_capacity(node));put<uint32_t>(f,bits);
 }
 f.close();if(!f)throw std::runtime_error("boundary output write");auto captured=stamp();
 std::ofstream boxes(std::string(directory)+"/boxes_"+std::to_string(iteration)+".bin",std::ios::binary);boxes.write("RCBOX001",8);put<uint64_t>(boxes,iteration);put<uint64_t>(boxes,routing.route_bb.size());
 for(auto netid:routing.route_bb.keys()){const auto& b=routing.route_bb[netid];put<uint64_t>(boxes,size_t(netid));put<int32_t>(boxes,b.xmin);put<int32_t>(boxes,b.xmax);put<int32_t>(boxes,b.ymin);put<int32_t>(boxes,b.ymax);put<int32_t>(boxes,b.layer_min);put<int32_t>(boxes,b.layer_max);}boxes.close();if(!boxes)throw std::runtime_error("box write");
 uint32_t pres_bits;std::memcpy(&pres_bits,&phase_pres,4);std::ofstream phase(std::string(directory)+"/phase.tsv",std::ios::app);phase<<iteration<<'\t'<<pres_bits<<'\t'<<phase_overused<<'\t'<<phase_total<<'\t'<<phase_worst<<'\t'<<phase_updated;for(float value:phase_timing){uint32_t bits;std::memcpy(&bits,&value,4);phase<<'\t'<<bits;}phase<<'\n';if(!phase)throw std::runtime_error("phase write");
 std::ofstream meta(std::string(directory)+"/boundary_times.tsv",std::ios::app);meta<<iteration<<'\t'<<device.rr_graph.num_nodes()<<'\t'<<begin<<'\t'<<printed<<'\t'<<captured<<'\n';if(!meta)throw std::runtime_error("boundary metadata write");
}

static void hash_bytes(uint64_t& h,const void* ptr,size_t n){const auto* p=static_cast<const unsigned char*>(ptr);for(size_t i=0;i<n;++i){h^=p[i];h*=1099511628211ULL;}}
template<class T> static void hash_word(uint64_t& h,T x){hash_bytes(h,&x,sizeof(x));}
static void probe_view(int iteration,uint64_t expected_rr,uint64_t expected_bb,const char* ledger){
 using namespace routecast_live;static Mapping mapping(std::getenv("ROUTECAST_LIVE_NET_MAP"),std::getenv("ROUTECAST_LIVE_IDENTITY"));static std::unique_ptr<View> prior;Scope scope(mapping,iteration);auto view=scope.view();auto expected=mapping.identity;expected.iteration=iteration;view.require(expected);int identity_rejected=0,expired_rejected=0;
 if(prior){try{prior->rr(0);throw std::runtime_error("old view accepted");}catch(const std::logic_error&){++expired_rejected;}}
 for(int field=0;field<7;++field){auto bad=expected;switch(field){case 0:bad.graph[0]=bad.graph[0]=='0'?'1':'0';break;case 1:bad.netlist[0]=bad.netlist[0]=='0'?'1':'0';break;case 2:bad.placement[0]=bad.placement[0]=='0'?'1':'0';break;case 3:bad.binary[0]=bad.binary[0]=='0'?'1':'0';break;case 4:bad.phase="wrong_phase";break;case 5:++bad.iteration;break;case 6:bad.case_tag="wrong_case";break;}try{view.require(bad);throw std::runtime_error("wrong identity accepted");}catch(const std::logic_error&){++identity_rejected;}}
 uint64_t rh=14695981039346656037ULL,bh=rh;for(size_t n=0;n<view.node_count();++n){auto rr=view.rr(n);hash_word<uint64_t>(rh,n);hash_word<uint32_t>(rh,rr.kind);hash_word<int32_t>(rh,rr.occupancy);hash_word<int32_t>(rh,rr.capacity);hash_word<uint32_t>(rh,rr.acc_bits);}
 for(size_t n=0;n<view.net_count();++n){auto net=view.net(n);auto box=view.box(net.endpoint);if(box.native!=net.native)throw std::runtime_error("native endpoint join");hash_word<uint64_t>(bh,box.native);for(auto x:box.coordinates)hash_word<int32_t>(bh,x);}
 if(rh!=expected_rr||bh!=expected_bb)throw std::runtime_error("view state mismatch");bool foreign_rejected=false;std::thread foreign([&](){try{view.rr(0);}catch(const std::logic_error&){foreign_rejected=true;}});foreign.join();if(!foreign_rejected)throw std::runtime_error("foreign thread view accepted");
 prior.reset(new View(view));scope.close();for(int field=0;field<4;++field){try{switch(field){case 0:view.rr(0);break;case 1:view.net(0);break;case 2:view.box(0);break;case 3:view.identity();break;}throw std::runtime_error("expired view accepted");}catch(const std::logic_error&){++expired_rejected;}}
 std::ofstream out(std::string(ledger)+".view.tsv",std::ios::app);out<<iteration<<'\t'<<mapping.entries.size()<<'\t'<<identity_rejected<<'\t'<<expired_rejected<<'\t'<<foreign_rejected<<'\t'<<rh<<'\t'<<bh<<'\n';if(!out)throw std::runtime_error("view ledger write");
}
static void consume_boundary(int iteration){
 const char* path=std::getenv("ROUTECAST_RESIDENT_CALLBACK_FILE");if(!path)return;
 auto begin=stamp();const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();uint64_t rh=14695981039346656037ULL,bh=rh,count=0,total=0,worst=0,elevated=0,channel_elevated=0;
 for(auto node:device.rr_graph.nodes()){
  const auto& state=routing.rr_node_route_inf[node];int32_t occ=state.occ(),cap=device.rr_graph.node_capacity(node);float acc=state.acc_cost;uint32_t bits;std::memcpy(&bits,&acc,4);uint32_t kind=uint32_t(device.rr_graph.node_type(node));
  if(occ<0||cap<=0||!std::isfinite(acc)||acc<1)throw std::runtime_error("consumer RR domain");
  uint64_t over=occ>cap?uint64_t(occ-cap):0;count+=over>0;total+=over;worst=std::max(worst,over);elevated+=acc>1;channel_elevated+=(kind==4||kind==5)&&acc>1;
  hash_word<uint64_t>(rh,size_t(node));hash_word<uint32_t>(rh,kind);hash_word<int32_t>(rh,occ);hash_word<int32_t>(rh,cap);hash_word<uint32_t>(rh,bits);
 }
 for(auto net:routing.route_bb.keys()){const auto& b=routing.route_bb[net];if(b.xmin<0||b.xmin>b.xmax||b.ymin<0||b.ymin>b.ymax||b.layer_min<0||b.layer_min>b.layer_max)throw std::runtime_error("consumer box domain");hash_word<uint64_t>(bh,size_t(net));for(int v:{b.xmin,b.xmax,b.ymin,b.ymax,b.layer_min,b.layer_max})hash_word<int32_t>(bh,v);}
 if(iteration!=phase_iteration||count!=phase_overused||total!=phase_total||worst!=phase_worst)throw std::runtime_error("consumer phase/overuse mismatch");
 probe_view(iteration,rh,bh,path);
 auto consumed=stamp();capture_boundary(iteration);auto captured=stamp();uint32_t pres_bits;std::memcpy(&pres_bits,&phase_pres,4);std::ofstream f(path,std::ios::app);f<<iteration<<'\t'<<device.rr_graph.num_nodes()<<'\t'<<routing.route_bb.size()<<'\t'<<pres_bits<<'\t'<<count<<'\t'<<total<<'\t'<<worst<<'\t'<<rh<<'\t'<<bh<<'\t'<<elevated<<'\t'<<channel_elevated<<'\t'<<begin<<'\t'<<consumed<<'\t'<<captured<<'\n';if(!f)throw std::runtime_error("callback ledger write");
}
extern "C" void WRAP(const Netlist<>& net,const char* place,const char* route,bool flat){REAL(net,place,route,flat);}
