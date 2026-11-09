#pragma once
#include "vpr_context.h"
#include "globals.h"
#include "routecast_preferred_checked_import.h"
#include <memory>
#include <fstream>
namespace routecast_native_preferred_v1 {
using Bank=vtr::vector<RRNodeId,t_rr_node_route_inf>;
struct View {
 Bank* bank;
 size_t size() const noexcept {return bank->size();}
 const void* identity() const noexcept {return bank;}
 float& word(size_t n) const noexcept {return (*bank)[RRNodeId(n)].acc_cost;}
};
using Frame=routecast_v2::QueryCostFrame<View>;
// Single shared serial router state across the private translation units.
inline std::unique_ptr<View> view;
inline std::unique_ptr<Frame> frame;
inline uint64_t query_count=0;
inline void initialize(const Netlist<>& nets,const std::string& digest,
                       const std::vector<std::pair<RRNodeId,float>>& pending_updates) {
 const char* path=std::getenv("ROUTECAST_PREFERRED_NET_CLAIMS");
 if(!path)return;
 if(!*path||frame||view)throw routecast_v2::FrameError("preferred context already active/empty path");
 auto& device=g_vpr_ctx.device();auto& routing=g_vpr_ctx.mutable_routing();
 routecast_import_v1::Context ctx;ctx.graph_sha256=digest;ctx.node_count=device.rr_graph.num_nodes();ctx.epoch=1;
 ctx.net_names.resize(nets.nets().size());ctx.ignored.resize(ctx.net_names.size());
 for(auto net:nets.nets()) {size_t n=size_t(net);if(n>=ctx.net_names.size())throw routecast_v2::FrameError("non-dense NET domain");ctx.net_names[n]=nets.net_name(net);ctx.ignored[n]=nets.net_is_ignored(net);}
 for(auto update:pending_updates)if(update.second!=1.f)ctx.expected_hint_bits.emplace(uint32_t(size_t(update.first)),routecast_v2::cost_bits(update.second));
 ctx.is_unit_channel=[&](uint32_t n){RRNodeId id(n);auto type=device.rr_graph.node_type(id);return (type==CHANX||type==CHANY)&&device.rr_graph.node_capacity(id)==1;};
 std::ifstream input(path);auto claims=routecast_import_v1::read(input,ctx);
 auto new_view=std::make_unique<View>();new_view->bank=&routing.rr_node_route_inf;
 auto new_frame=std::make_unique<Frame>(*new_view,uint32_t(ctx.net_names.size()),1,claims,true,1);
 view=std::move(new_view);frame=std::move(new_frame);query_count=0;
}
class Scope {
 Frame* owner_=nullptr;routecast_v2::FrameToken token_{};
public:
 Scope(uint32_t net,int iteration) {
  if(frame) {if(iteration<1)throw routecast_v2::FrameError("iteration domain");owner_=frame.get();token_=owner_->begin(1,net,uint32_t(iteration));++query_count;}
 }
 Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
 ~Scope() noexcept {if(owner_)try{owner_->finish(token_);}catch(...){std::terminate();}}
};
inline void finish() {
 if(frame&&frame->active())throw routecast_v2::FrameError("unclosed preferred query");
 frame.reset();view.reset();
}
}
