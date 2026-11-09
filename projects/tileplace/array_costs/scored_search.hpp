#pragma once
#include "../hbm_abi/flat_search_metadata.hpp"
#include "../hbm_abi/strict_flat_state.hpp"
#include "scored_proposals.hpp"
#include "../hbm_abi/candidate_root_array.hpp"
#include "../hbm_abi/trial_legality_array.hpp"
#include "../hbm_abi/macro_translation_array.hpp"
#include "../hbm_abi/guard_array.hpp"
#include "../hbm_abi/occupancy_array.hpp"
#include "../hbm_abi/macro_shape_array.hpp"
namespace tileplace_hbm {
// CPU search from strict binary metadata; STL candidate enumeration remains.
class ScoredArraySearch {
 FlatSearchMetadata metadata_;
 StrictFlatState state_;
 std::vector<Site> sites_;
 std::vector<Block> blocks_;
 std::vector<Region> regions_;
public:
 explicit ScoredArraySearch(const std::vector<std::uint8_t>& bytes):metadata_(bytes),state_(bytes){
  for(const auto& [p,t]:metadata_.constraints().sites)sites_.push_back({{p.x,p.y,p.subtile,p.layer},std::uint32_t(std::stoul(t)),{0,0,0}});
  for(const auto& [id,b]:metadata_.constraints().blocks){
   Block record{};record.id=id;record.type_id=std::stoul(b.type);
   record.regions.offset=regions_.size();
   if(b.regions){record.fixed_mask|=0x80000000u;
    for(const auto&r:*b.regions)regions_.push_back({r.xmin,r.ymin,r.xmax,r.ymax,r.layer_low,r.layer_high,r.subtile,0});
    record.regions.count=b.regions->size();
   }
   for(unsigned i=0;i<4;++i)if(b.fixed[i]){record.fixed_mask|=1u<<i;record.fixed[i]=*b.fixed[i];}
   blocks_.push_back(record);
  }

  if(metadata_.units().size()>UINT32_MAX)throw std::overflow_error("unit count overflow");
  for(std::size_t i=0;i<metadata_.units().size();++i)for(auto id:metadata_.units()[i])blocks_.at(translation_index(blocks_.data(),blocks_.size(),id)).unit_id=i;

 }
 const auto& positions() const{return state_.positions();}
 auto snapshot() const{return state_.snapshot();}
 void restore(const FlatState::Snapshot& saved){state_.restore(saved);}
 void commit(const tileplace_snapshot::Positions& changes){state_.commit(changes);}
 auto proposals(unsigned selector,bool color,const tileplace_snapshot::CallbackProposalConfig& config,
  const std::set<tileplace_snapshot::ProposalIdentity>& forbidden={},
  const std::vector<tileplace_snapshot::CallbackGuard>& guards={},tileplace_snapshot::TransactionColorStats* stats=nullptr) const {
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
  std::vector<Location> current;for(const auto& b:blocks_){auto p=positions().at(b.id);current.push_back({p.x,p.y,p.subtile,p.layer});}
  auto valid=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX)throw std::overflow_error("trial count overflow");
   std::vector<TrialMove> moves;for(const auto& [id,p]:trial)moves.push_back({id,{p.x,p.y,p.subtile,p.layer}});
   std::uint32_t status;
   auto result=trial_legality_array(blocks_.data(),current.data(),blocks_.size(),sites_.data(),sites_.size(),regions_.data(),regions_.size(),moves.data(),moves.size(),status);
   if(status)throw std::invalid_argument("array legality input rejected");
   return result;
  };
  auto translate=[&](const tileplace_snapshot::Unit& unit,tileplace_snapshot::Point target){
   if(unit.size()>UINT32_MAX)throw std::overflow_error("macro count overflow");
   std::vector<TrialMove> out(unit.size());std::uint32_t status;
   auto count=macro_translation_array(blocks_.data(),current.data(),blocks_.size(),unit.data(),unit.size(),{target.x,target.y,target.subtile,target.layer},out.data(),out.size(),status);
   if(status==4)throw std::overflow_error("translated coordinate overflow");
   if(status)throw std::invalid_argument("array macro input rejected");
   tileplace_snapshot::Positions result;
   for(unsigned i=0;i<count;++i){auto p=out[i].target;result[out[i].id]={p.x,p.y,p.subtile,p.layer};}
   return result;
  };
  std::vector<ArrayGuard> checked_guards;for(const auto& g:guards)checked_guards.push_back({g.source,g.sink,g.maximum});
  auto guard_ok=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX)throw std::overflow_error("guard move count overflow");
   std::vector<TrialMove> moves;for(const auto& [id,p]:trial)moves.push_back({id,{p.x,p.y,p.subtile,p.layer}});
   std::uint32_t status;auto result=guard_array(blocks_.data(),current.data(),blocks_.size(),moves.data(),moves.size(),checked_guards.data(),checked_guards.size(),status);
   if(status)throw std::invalid_argument("array guard input rejected");
   return result;
  };
  auto occupy=[&](tileplace_snapshot::Point p){return occupancy_array(blocks_.data(),current.data(),blocks_.size(),{p.x,p.y,p.subtile,p.layer});};
  auto same_shape=[&](const tileplace_snapshot::Unit& a,const tileplace_snapshot::Unit& b){
   if(a.size()>UINT32_MAX||b.size()>UINT32_MAX)throw std::overflow_error("shape count overflow");
   std::uint32_t status;auto result=macro_shape_array(blocks_.data(),current.data(),blocks_.size(),a.data(),a.size(),b.data(),b.size(),status);
   if(status)throw std::invalid_argument("array shape input rejected");
   return result;
  };
  auto result=color?tileplace_snapshot::scored_array_propose_color(selector,metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,valid,translate,guard_ok,occupy,same_shape,config,metadata_.focus(),forbidden,guards,stats):
   tileplace_snapshot::scored_array_proposals_for_unit(metadata_.units().at(selector),metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,valid,translate,guard_ok,occupy,same_shape,config,guards);
  for(auto& proposal:result){std::set<std::uint32_t> ids;for(auto index:proposal.touched_nets)ids.insert(metadata_.net_ids().at(index));proposal.touched_nets=std::move(ids);}
  return result;
 }
};
}
