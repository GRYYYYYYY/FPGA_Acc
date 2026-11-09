#pragma once
#include "globals.h"
#include "vpr_context.h"
#include <atomic>
#include <memory>
#include <thread>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <set>
#include <stdexcept>
#include <array>
#include <cstring>
namespace routecast_live {
struct Identity {std::string graph,netlist,placement,binary,phase,case_tag;int iteration=0;bool operator==(const Identity& b)const{return graph==b.graph&&netlist==b.netlist&&placement==b.placement&&binary==b.binary&&phase==b.phase&&case_tag==b.case_tag&&iteration==b.iteration;}};
struct Net {size_t native,endpoint;std::string name;bool ignored;};
struct RR {uint32_t kind;int32_t occupancy,capacity;uint32_t acc_bits;};
struct Box {size_t native,endpoint;std::array<int32_t,6> coordinates;};
inline const char* phase_name(){return "post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance";}
struct Mapping {
 std::vector<Net> entries;std::vector<size_t> inverse;Identity identity;
 Mapping(const char* path,const char* idpath){
  if(!path||!idpath)throw std::runtime_error("missing live mapping/identity");std::ifstream f(path);std::string line;std::set<size_t> endpoints;
  while(std::getline(f,line)){std::istringstream s(line);std::string n,e,g,name;if(!std::getline(s,n,'\t')||!std::getline(s,e,'\t')||!std::getline(s,g,'\t')||!std::getline(s,name))throw std::runtime_error("mapping row");if(n.empty()||e.empty()||n.find_first_not_of("0123456789")!=std::string::npos||e.find_first_not_of("0123456789")!=std::string::npos)throw std::runtime_error("mapping integer");size_t native=std::stoull(n),endpoint=std::stoull(e);if(native!=entries.size()||!endpoints.insert(endpoint).second||(g!="0"&&g!="1"))throw std::runtime_error("mapping domain");entries.push_back({native,endpoint,name,g=="1"});}
  const auto& list=g_vpr_ctx.clustering().clb_nlist;if(entries.size()!=list.nets().size())throw std::runtime_error("mapping size");inverse.resize(entries.size());for(auto net:list.nets()){size_t n=size_t(net);if(n>=entries.size()||entries[n].name!=list.net_name(net)||entries[n].ignored!=list.net_is_ignored(net)||entries[n].endpoint>=inverse.size())throw std::runtime_error("live NET identity");inverse[entries[n].endpoint]=n;}
  std::ifstream ids(idpath);if(!std::getline(ids,identity.graph)||!std::getline(ids,identity.netlist)||!std::getline(ids,identity.placement)||!std::getline(ids,identity.binary)||!std::getline(ids,identity.phase)||!std::getline(ids,identity.case_tag)||identity.case_tag.empty())throw std::runtime_error("identity row");for(const auto* hash:{&identity.graph,&identity.netlist,&identity.placement,&identity.binary})if(hash->size()!=64||hash->find_first_not_of("0123456789abcdef")!=std::string::npos)throw std::runtime_error("identity digest domain");if(identity.phase!=phase_name())throw std::runtime_error("identity phase");
 }
};
class Scope;
class View {
 struct Epoch {std::atomic<bool> active{true};std::thread::id owner=std::this_thread::get_id();};
 std::shared_ptr<Epoch> epoch_;const Mapping* mapping_;Identity identity_;
 View(std::shared_ptr<Epoch> e,const Mapping& m,int i):epoch_(std::move(e)),mapping_(&m),identity_(m.identity){identity_.iteration=i;}
 void check()const{if(!epoch_->active.load(std::memory_order_acquire)||epoch_->owner!=std::this_thread::get_id())throw std::logic_error("expired_or_foreign_callback_view");}
 friend class Scope;
public:
 Identity identity()const{check();return identity_;}
 void require(const Identity& expected)const{check();if(!(expected==identity_))throw std::logic_error("view_identity_mismatch");}
 size_t node_count()const{check();return g_vpr_ctx.device().rr_graph.num_nodes();}
 size_t net_count()const{check();return mapping_->entries.size();}
 Net net(size_t native)const{check();return mapping_->entries.at(native);}
 RR rr(size_t index)const{check();if(index>=node_count())throw std::out_of_range("RR index");auto node=RRNodeId(index);const auto& device=g_vpr_ctx.device();const auto& r=g_vpr_ctx.routing().rr_node_route_inf[node];uint32_t bits;float a=r.acc_cost;std::memcpy(&bits,&a,4);return {uint32_t(device.rr_graph.node_type(node)),r.occ(),device.rr_graph.node_capacity(node),bits};}
 Box box(size_t endpoint)const{check();size_t native=mapping_->inverse.at(endpoint);const auto& b=g_vpr_ctx.routing().route_bb[ParentNetId(native)];return {native,endpoint,{{b.xmin,b.xmax,b.ymin,b.ymax,b.layer_min,b.layer_max}}};}
};
class Scope {
 std::shared_ptr<View::Epoch> epoch_=std::make_shared<View::Epoch>();View view_;
public:
 Scope(const Mapping& m,int i):view_(epoch_,m,i){}Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
 View view()const{return view_;}void close(){epoch_->active.store(false,std::memory_order_release);}~Scope(){close();}
};
}
