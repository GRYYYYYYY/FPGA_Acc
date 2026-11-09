#pragma once
#include "../wire_control_commit/host_snapshot_words.hpp"
#include "../wire_full_color_capacity_query/host_scratch_words.hpp"
#include "../wire_control_commit/host_propose.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include "../hbm_abi/flat_search_metadata.hpp"
#include "wire_cost_state.hpp"
#include "transaction_proposals.hpp"
#include "../wire_enumerator/enumerate_words.hpp"
#include "../wire_trial_build/chain_words.hpp"
#include "../wire_trial_build/merge_words.hpp"
#include "../wire_enumeration/owners_words.hpp"
#include "../wire_control/eligible_words.hpp"
#include "../wire_pipeline/touched_words.hpp"
#include "../wire_pipeline/write_sites_words.hpp"
#include "../wire_candidates/root_words.hpp"
#include "../hbm_abi/trial_legality_array.hpp"
#include "../wire_legality/trial_words.hpp"
#include "../wire_candidates/translation_words.hpp"
#include "../wire_checks/guard_words.hpp"
#include "../hbm_abi/occupancy_array.hpp"
#include "../wire_checks/occupancy_shape_words.hpp"
namespace tileplace_hbm {
// CPU search from strict binary metadata; STL candidate enumeration remains.
class WireEnumSearch {
 std::vector<std::uint8_t> full_bytes_;
 FlatSearchMetadata metadata_;
 WireCostState state_;
 std::vector<Site> sites_;
 std::vector<Block> blocks_;
 std::vector<Region> regions_;
 std::vector<std::uint64_t> bw_,sw_,rw_,nw_,uw_;
 std::vector<std::uint32_t> unit_members_,focus_;
 std::vector<std::uint32_t> net_members_;
 std::map<std::uint32_t,std::uint32_t> net_indices_;
 static std::uint64_t packed(std::int32_t a,std::int32_t b){return std::uint32_t(a)|(std::uint64_t(std::uint32_t(b))<<32);}
public:
 explicit WireEnumSearch(const std::vector<std::uint8_t>& bytes):full_bytes_(bytes),metadata_(bytes),state_(bytes){
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

  for(const auto& b:blocks_)bw_.insert(bw_.end(),{std::uint64_t(b.id)|(std::uint64_t(b.type_id)<<32),0,0,b.regions.offset,b.regions.count,packed(b.fixed[0],b.fixed[1]),packed(b.fixed[2],b.fixed[3]),std::uint64_t(b.fixed_mask)|(std::uint64_t(b.unit_id)<<32)});
  if(metadata_.nets().size()>UINT32_MAX)throw std::overflow_error("net count overflow");
  for(std::size_t i=0;i<metadata_.nets().size();++i){const auto& n=metadata_.nets()[i];auto id=metadata_.net_ids().at(i);net_indices_[id]=i;nw_.insert(nw_.end(),{id,0,net_members_.size(),n.members.size(),0,0});net_members_.insert(net_members_.end(),n.members.begin(),n.members.end());}
  for(const auto& u:metadata_.units()){uw_.insert(uw_.end(),{unit_members_.size(),u.size(),metadata_.fixed().count(u)?1ULL:0ULL,0});unit_members_.insert(unit_members_.end(),u.begin(),u.end());}
  focus_.assign(metadata_.focus().begin(),metadata_.focus().end());
  for(const auto& s:sites_)sw_.insert(sw_.end(),{packed(s.location.x,s.location.y),packed(s.location.subtile,s.location.layer),s.type_id,0});
  for(const auto& r:regions_)rw_.insert(rw_.end(),{packed(r.xmin,r.ymin),packed(r.xmax,r.ymax),packed(r.layer_low,r.layer_high),packed(r.subtile,0)});

 }
 const auto& positions() const{return state_.positions();}
 auto snapshot() const{return state_.snapshot();}
 void restore(const WireCostState::Snapshot& saved){state_.restore(saved);}
 void commit(const tileplace_snapshot::Positions& changes){state_.commit(changes);}
 auto proposals(unsigned selector,bool color,const tileplace_snapshot::CallbackProposalConfig& config,
  const std::set<tileplace_snapshot::ProposalIdentity>& forbidden={},
  const std::vector<tileplace_snapshot::CallbackGuard>& guards={},tileplace_snapshot::TransactionColorStats* stats=nullptr) const {
  if(color){
   auto bytes=full_bytes_;auto start=224+64ULL*blocks_.size();
   for(std::size_t i=0;i<blocks_.size();++i){const auto& p=positions().at(blocks_[i].id);std::uint64_t words[2]={packed(p.x,p.y),packed(p.subtile,p.layer)};for(unsigned j=0;j<16;++j)bytes.at(start+16*i+j)=std::uint8_t(words[j/8]>>(8*(j%8)));}
   tileplace_wire_control_commit::HostSnapshotWords snapshot(bytes);auto input=snapshot.input();input.color=selector;input.width=config.page_width;input.height=config.page_height;input.limit=config.candidate_limit;input.chain_limit=config.chain_limit;input.weights=config.weights.data();
   std::vector<std::uint64_t> guard_words;for(const auto& g:guards)guard_words.insert(guard_words.end(),{std::uint64_t(g.source)|(std::uint64_t(g.sink)<<32),g.maximum});input.guards=guard_words.data();input.guard_count=guards.size();
   std::vector<tileplace_snapshot::Proposal> placeholders;for(const auto& id:forbidden){tileplace_snapshot::Proposal p;p.kind=std::get<0>(id);p.units=std::get<1>(id);p.trial=std::get<2>(id);placeholders.push_back(std::move(p));}
   tileplace_wire_transactions::Encoded blocked(std::move(placeholders));std::vector<std::uint64_t> identities;for(std::size_t i=0;i<blocked.proposals.size();++i){auto r=blocked.rw.data()+13*i;identities.insert(identities.end(),r+1,r+7);}
   tileplace_wire_control_commit::ExternalForbidden external{identities.data(),unsigned(blocked.proposals.size()),{blocked.kinds.data(),blocked.kinds.size(),blocked.iw.data(),blocked.iw.size()/2,blocked.members.data(),blocked.members.size(),blocked.tw.data(),blocked.tw.size()/3}};input.external_forbidden=&external;
   tileplace_wire_control_commit::HostColorScratch scratch(input);auto output=tileplace_wire_control_commit::propose(input,scratch.view());
   if(stats){*stats={};stats->eligible=output.stats.eligible;stats->proposals=output.stats.proposals;stats->accepted=output.stats.accepted;stats->rejected=output.stats.rejected;const std::string names[5]={"move","swap","macro_swap","chain2","chain3"};for(unsigned k=0;k<5;++k)if(output.stats.kinds[k])stats->kinds[names[k]]=output.stats.kinds[k];}
   return output.proposals;
  }
  auto evaluate=[&](const std::set<std::uint32_t>& indices,const tileplace_snapshot::Positions& changes){
   std::set<std::uint32_t> ids;for(auto index:indices)ids.insert(metadata_.net_ids().at(index));
   return state_.evaluate(ids,changes);
  };
  auto roots=[&](const tileplace_snapshot::Unit& unit,std::size_t requested){
   auto p=positions().at(unit.front());auto capacity=std::min(requested,sites_.size());
   if(capacity>UINT32_MAX)throw std::overflow_error("root capacity overflow");
   std::vector<std::uint64_t> out(2*capacity);std::uint32_t status;
   std::uint64_t source[2]={packed(p.x,p.y),packed(p.subtile,p.layer)};
   auto count=tileplace_wire_candidates::roots(sw_.data(),sites_.size(),source,std::stoul(metadata_.constraints().blocks.at(unit.front()).type),config.page_width,config.page_height,capacity,out.data(),capacity,status);
   if(status)throw std::invalid_argument("wire root query failed");
   std::vector<tileplace_snapshot::Point> result;
   for(unsigned i=0;i<count;++i){auto q=tileplace_wire_candidates::location(out.data()+2ULL*i);result.push_back({q.x,q.y,q.subtile,q.layer});}
   return result;
  };
  std::vector<Location> current;for(const auto& b:blocks_){auto p=positions().at(b.id);current.push_back({p.x,p.y,p.subtile,p.layer});}
  std::vector<std::uint64_t> pw;for(auto p:current){pw.push_back(packed(p.x,p.y));pw.push_back(packed(p.subtile,p.layer));}
  auto valid=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX)throw std::overflow_error("trial count overflow");
   std::vector<std::uint64_t> moves;for(const auto& [id,p]:trial){moves.push_back(id);moves.push_back(packed(p.x,p.y));moves.push_back(packed(p.subtile,p.layer));}
   std::uint32_t status;auto result=tileplace_wire_legality::trial(bw_.data(),pw.data(),blocks_.size(),sw_.data(),sites_.size(),rw_.data(),regions_.size(),moves.data(),trial.size(),status);
   if(status)throw std::invalid_argument("wire legality input rejected");
   return result;
  };
  auto translate=[&](const tileplace_snapshot::Unit& unit,tileplace_snapshot::Point target){
   if(unit.size()>UINT32_MAX)throw std::overflow_error("macro count overflow");
   std::vector<std::uint64_t> out(3*unit.size());std::uint32_t status;
   std::uint64_t target_words[2]={packed(target.x,target.y),packed(target.subtile,target.layer)};
   auto count=tileplace_wire_candidates::translate(bw_.data(),pw.data(),blocks_.size(),unit.data(),unit.size(),target_words,out.data(),unit.size(),status);
   if(status==4)throw std::overflow_error("translated coordinate overflow");
   if(status)throw std::invalid_argument("wire macro input rejected");
   tileplace_snapshot::Positions result;
   for(unsigned i=0;i<count;++i){auto p=tileplace_wire_candidates::location(out.data()+3ULL*i+1);result[std::uint32_t(out[3ULL*i])]={p.x,p.y,p.subtile,p.layer};}
   return result;
  };
  std::vector<std::uint64_t> checked_guards;for(const auto& g:guards){checked_guards.push_back(std::uint64_t(g.source)|(std::uint64_t(g.sink)<<32));checked_guards.push_back(g.maximum);}
  auto guard_ok=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX)throw std::overflow_error("guard move count overflow");
   std::vector<std::uint64_t> moves;for(const auto& [id,p]:trial){moves.push_back(id);moves.push_back(packed(p.x,p.y));moves.push_back(packed(p.subtile,p.layer));}
   std::uint32_t status;auto result=tileplace_wire_checks::guards(bw_.data(),pw.data(),blocks_.size(),moves.data(),trial.size(),checked_guards.data(),guards.size(),status);
   if(status)throw std::invalid_argument("array guard input rejected");
   return result;
  };
  auto occupy=[&](tileplace_snapshot::Point p){std::uint64_t query[2]={packed(p.x,p.y),packed(p.subtile,p.layer)};std::uint32_t status;auto result=tileplace_wire_checks::occupant(bw_.data(),pw.data(),blocks_.size(),query,status);if(status)throw std::invalid_argument("wire occupancy input rejected");return result;};
  auto same_shape=[&](const tileplace_snapshot::Unit& a,const tileplace_snapshot::Unit& b){
   if(a.size()>UINT32_MAX||b.size()>UINT32_MAX)throw std::overflow_error("shape count overflow");
   std::uint32_t status;auto result=tileplace_wire_checks::shape(bw_.data(),pw.data(),blocks_.size(),a.data(),a.size(),b.data(),b.size(),status);
   if(status)throw std::invalid_argument("array shape input rejected");
   return result;
  };
  auto touched_indices=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX)throw std::overflow_error("touch move count overflow");
   std::vector<std::uint64_t> moves;for(const auto& [id,p]:trial){moves.push_back(id);moves.push_back(packed(p.x,p.y));moves.push_back(packed(p.subtile,p.layer));}
   std::vector<std::uint32_t> ids(metadata_.nets().size());std::uint32_t status;
   auto count=tileplace_wire_pipeline::touched(nw_.data(),metadata_.nets().size(),net_members_.data(),net_members_.size(),moves.data(),trial.size(),ids.data(),ids.size(),status);
   if(status)throw std::invalid_argument("wire touched-net input rejected");
   std::set<std::uint32_t> result;for(unsigned i=0;i<count;++i)result.insert(net_indices_.at(ids[i]));return result;
  };
  auto write_set=[&](const tileplace_snapshot::Positions& trial){
   if(trial.size()>UINT32_MAX/2)throw std::overflow_error("write-site count overflow");
   std::vector<std::uint64_t> moves;for(const auto& [id,p]:trial){moves.push_back(id);moves.push_back(packed(p.x,p.y));moves.push_back(packed(p.subtile,p.layer));}
   auto capacity=2*trial.size();std::vector<std::uint64_t> words(2*capacity);
   auto out=tileplace_wire_pipeline::write_sites(bw_.data(),pw.data(),blocks_.size(),moves.data(),trial.size(),words.data(),capacity);
   if(out.status)throw std::invalid_argument("wire write-site input rejected");
   std::set<tileplace_snapshot::Point> result;for(unsigned i=0;i<out.count;++i){auto p=tileplace_wire_candidates::location(words.data()+2ULL*i);result.insert({p.x,p.y,p.subtile,p.layer});}return std::make_pair(bool(out.changed),std::move(result));
  };
  auto classify_owners=[&](const tileplace_snapshot::Unit& unit,const tileplace_snapshot::Positions& trial){
   if(unit.size()>UINT32_MAX||trial.size()>UINT32_MAX)throw std::overflow_error("owner move count overflow");
   std::vector<std::uint64_t> moves;for(const auto& [id,p]:trial){moves.push_back(id);moves.push_back(packed(p.x,p.y));moves.push_back(packed(p.subtile,p.layer));}
   auto out=tileplace_wire_enumeration::owners(bw_.data(),pw.data(),blocks_.size(),unit.data(),unit.size(),moves.data(),trial.size());if(out.status)throw std::invalid_argument("wire owner input rejected");return out;
  };
  auto merge_trials=[&](const tileplace_snapshot::Positions& a,const tileplace_snapshot::Positions& b){
   if(a.size()>UINT32_MAX||b.size()>UINT32_MAX||a.size()+b.size()>UINT32_MAX)throw std::overflow_error("merged trial count overflow");
   auto encode=[&](const tileplace_snapshot::Positions& trial){std::vector<std::uint64_t> words;for(const auto& [id,p]:trial){words.push_back(id);words.push_back(packed(p.x,p.y));words.push_back(packed(p.subtile,p.layer));}return words;};
   auto aw=encode(a),bw=encode(b);std::vector<std::uint64_t> words(3*(a.size()+b.size()));std::uint32_t status;auto count=tileplace_wire_trial_build::merge(aw.data(),a.size(),bw.data(),b.size(),words.data(),a.size()+b.size(),status);if(status)throw std::invalid_argument("wire merge input rejected");
   tileplace_snapshot::Positions result;for(unsigned i=0;i<count;++i){auto p=tileplace_wire_candidates::location(words.data()+3ULL*i+1);result[std::uint32_t(words[3ULL*i])]={p.x,p.y,p.subtile,p.layer};}return result;
  };
  auto build_chain=[&](const std::vector<std::uint32_t>& ids,tileplace_snapshot::Point target,tileplace_snapshot::Point next){
   std::uint64_t tw[2]={packed(target.x,target.y),packed(target.subtile,target.layer)},nw[2]={packed(next.x,next.y),packed(next.subtile,next.layer)},words[9]{};std::uint32_t status;
   auto count=tileplace_wire_trial_build::chain(bw_.data(),pw.data(),blocks_.size(),ids.data(),ids.size(),tw,nw,words,3,status);if(status)throw std::invalid_argument("wire chain input rejected");
   tileplace_snapshot::Positions result;for(unsigned i=0;i<count;++i){auto p=tileplace_wire_candidates::location(words+3*i+1);result[std::uint32_t(words[3*i])]={p.x,p.y,p.subtile,p.layer};}return result;
  };
  auto enumerate_trials=[&](const tileplace_snapshot::Unit& unit,auto emit){
   auto found=std::lower_bound(metadata_.units().begin(),metadata_.units().end(),unit);if(found==metadata_.units().end()||*found!=unit)throw std::invalid_argument("enumeration unit missing");auto index=found-metadata_.units().begin();
   auto limit=std::min(std::size_t(config.candidate_limit),sites_.size()),chain_limit=std::min(std::size_t(config.chain_limit),sites_.size());
   std::size_t max_members=0;for(const auto& u:metadata_.units())max_members=std::max(max_members,u.size());auto capacity=std::max(std::size_t(3),2*max_members);if(capacity>UINT32_MAX||limit>UINT32_MAX||chain_limit>UINT32_MAX)throw std::overflow_error("enumeration capacity overflow");
   std::vector<std::uint64_t> roots(2*limit),chain_roots(2*chain_limit),first(3*capacity),second(3*capacity),merged(3*capacity);std::uint32_t status;
   const char* names[]={"move","swap","macro_swap","chain2","chain3"};
   auto sink=[&](unsigned kind,const unsigned* moved,unsigned moved_count,const std::uint64_t* moves,unsigned count){std::vector<tileplace_snapshot::Unit> owners;for(unsigned i=0;i<moved_count;++i)owners.push_back(metadata_.units().at(moved[i]));tileplace_snapshot::Positions trial;for(unsigned i=0;i<count;++i){auto p=tileplace_wire_candidates::location(moves+3ULL*i+1);trial[std::uint32_t(moves[3ULL*i])]={p.x,p.y,p.subtile,p.layer};}emit(names[kind],std::move(owners),std::move(trial));};
   tileplace_wire_enumerator::enumerate(index,uw_.data(),metadata_.units().size(),unit_members_.data(),bw_.data(),pw.data(),blocks_.size(),sw_.data(),sites_.size(),config.page_width,config.page_height,limit,chain_limit,roots.data(),limit,chain_roots.data(),chain_limit,first.data(),second.data(),merged.data(),capacity,sink,status);
   if(status)throw std::invalid_argument("wire enumeration input rejected");
  };
  std::vector<std::uint32_t> eligible_indices;
  if(color){eligible_indices.resize(metadata_.units().size());std::uint32_t status;auto count=tileplace_wire_control::eligible(uw_.data(),metadata_.units().size(),unit_members_.data(),unit_members_.size(),focus_.data(),focus_.size(),bw_.data(),pw.data(),blocks_.size(),config.page_width,config.page_height,selector,eligible_indices.data(),eligible_indices.size(),status);if(status)throw std::invalid_argument("wire eligible input rejected");eligible_indices.resize(count);}
  auto result=color?tileplace_snapshot::wire_transaction_propose_color(selector,metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,valid,translate,guard_ok,occupy,same_shape,touched_indices,write_set,classify_owners,merge_trials,build_chain,enumerate_trials,config,eligible_indices,forbidden,guards,stats):
   tileplace_snapshot::wire_transaction_proposals_for_unit(metadata_.units().at(selector),metadata_.units(),metadata_.fixed(),positions(),metadata_.constraints(),metadata_.nets(),evaluate,roots,valid,translate,guard_ok,occupy,same_shape,touched_indices,write_set,classify_owners,merge_trials,build_chain,enumerate_trials,config,guards);
  for(auto& proposal:result){std::set<std::uint32_t> ids;for(auto index:proposal.touched_nets)ids.insert(metadata_.net_ids().at(index));proposal.touched_nets=std::move(ids);}
  return result;
 }
};
}
