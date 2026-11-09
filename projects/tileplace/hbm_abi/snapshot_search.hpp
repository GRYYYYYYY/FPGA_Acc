#pragma once
#include "flat_search_metadata.hpp"
#include "strict_flat_state.hpp"
namespace tileplace_hbm {
// CPU search from strict binary metadata; STL candidate enumeration remains.
class SnapshotSearch {
 FlatSearchMetadata metadata_;
 StrictFlatState state_;
public:
 explicit SnapshotSearch(const std::vector<std::uint8_t>& bytes):metadata_(bytes),state_(bytes){}
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
  auto result=color?tileplace_snapshot::callback_propose_color(selector,metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,config,metadata_.focus(),forbidden,guards):
   tileplace_snapshot::callback_proposals_for_unit(metadata_.units().at(selector),metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,config,guards);
  for(auto& proposal:result){std::set<std::uint32_t> ids;for(auto index:proposal.touched_nets)ids.insert(metadata_.net_ids().at(index));proposal.touched_nets=std::move(ids);}
  return result;
 }
};
}
