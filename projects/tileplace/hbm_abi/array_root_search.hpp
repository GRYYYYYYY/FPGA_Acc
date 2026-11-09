#pragma once
#include "flat_search_metadata.hpp"
#include "strict_flat_state.hpp"
#include "array_root_proposals.hpp"
#include "candidate_root_array.hpp"
namespace tileplace_hbm {
// CPU search from strict binary metadata; STL candidate enumeration remains.
class ArrayRootSearch {
 FlatSearchMetadata metadata_;
 StrictFlatState state_;
 std::vector<Site> sites_;
public:
 explicit ArrayRootSearch(const std::vector<std::uint8_t>& bytes):metadata_(bytes),state_(bytes){
  for(const auto& [p,t]:metadata_.constraints().sites)sites_.push_back({{p.x,p.y,p.subtile,p.layer},std::uint32_t(std::stoul(t)),{0,0,0}});
 }
 const auto& positions() const{return state_.positions();}
 auto snapshot() const{return state_.snapshot();}
 void restore(const FlatState::Snapshot& saved){state_.restore(saved);}
 void commit(const tileplace_snapshot::Positions& changes){state_.commit(changes);}
 auto proposals(unsigned selector,bool color,const tileplace_snapshot::CallbackProposalConfig& config,
  const std::set<tileplace_snapshot::ProposalIdentity>& forbidden={},
  const std::vector<tileplace_snapshot::CallbackGuard>& guards={}) const {
  auto evaluate=[&](const std::set<std::uint32_t>& indices,const tileplace_snapshot::Positions& changes){
   std::set<std::uint32_t> ids;for(auto index:indices)ids.insert(metadata_.net_ids().at(index));
   return state_.evaluate(ids,changes);
  };
  auto roots=[&](const tileplace_snapshot::Unit& unit,std::size_t requested){
   auto p=positions().at(unit.front());auto capacity=std::min(requested,sites_.size());
   if(capacity>UINT32_MAX)throw std::overflow_error("root capacity overflow");
   std::vector<Location> out(capacity);std::uint32_t status;
   auto count=candidate_root_array(sites_.data(),sites_.size(),{p.x,p.y,p.subtile,p.layer},std::stoul(metadata_.constraints().blocks.at(unit.front()).type),config.page_width,config.page_height,capacity,out.data(),capacity,status);
   if(status)throw std::invalid_argument("array root query failed");
   std::vector<tileplace_snapshot::Point> result;
   for(unsigned i=0;i<count;++i)result.push_back({out[i].x,out[i].y,out[i].subtile,out[i].layer});
   return result;
  };
  auto result=color?tileplace_snapshot::array_root_propose_color(selector,metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,config,metadata_.focus(),forbidden,guards):
   tileplace_snapshot::array_root_proposals_for_unit(metadata_.units().at(selector),metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,config,guards);
  for(auto& proposal:result){std::set<std::uint32_t> ids;for(auto index:proposal.touched_nets)ids.insert(metadata_.net_ids().at(index));proposal.touched_nets=std::move(ids);}
  return result;
 }
};
}
