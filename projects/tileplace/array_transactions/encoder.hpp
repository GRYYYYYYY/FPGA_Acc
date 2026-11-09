#pragma once
#include "identity_selection.hpp"
#include "../cpp_snapshot/transactions.hpp"
namespace tileplace_transaction_array {
// CPU host encoder. Core ordering/selection uses only the arrays below.
struct Encoded {
 std::vector<tileplace_snapshot::Proposal> proposals;
 std::vector<IdentityRecord> records;
 std::vector<std::uint8_t> kinds;
 std::vector<Range> identity_units;
 std::vector<std::uint32_t> members,nets,units;
 std::vector<tileplace_hbm::TrialMove> trials;
 std::vector<Location> sites;
 explicit Encoded(std::vector<tileplace_snapshot::Proposal> input):proposals(std::move(input)){
  if(proposals.size()>UINT32_MAX)throw std::length_error("transaction count overflow");
  std::map<tileplace_snapshot::Unit,std::uint32_t> owners;
  for(auto& p:proposals){std::sort(p.units.begin(),p.units.end());for(const auto& u:p.units)owners.emplace(u,0);}
  if(owners.size()>UINT32_MAX)throw std::length_error("unit identity count overflow");
  std::uint32_t index=0;for(auto& item:owners)item.second=index++;
  for(const auto& p:proposals){
   Identity id{{kinds.size(),p.kind.size()},{identity_units.size(),p.units.size()},{trials.size(),p.trial.size()}};
   IdentityRecord record{p.score,id,{sites.size(),p.write_sites.size()},{nets.size(),p.touched_nets.size()},{units.size(),p.units.size()}};
   kinds.insert(kinds.end(),p.kind.begin(),p.kind.end());
   for(const auto& u:p.units){identity_units.push_back({members.size(),u.size()});members.insert(members.end(),u.begin(),u.end());units.push_back(owners.at(u));}
   for(const auto& [block,p]:p.trial)trials.push_back({block,{p.x,p.y,p.subtile,p.layer}});
   for(auto p:p.write_sites)sites.push_back({p.x,p.y,p.subtile,p.layer});
   nets.insert(nets.end(),p.touched_nets.begin(),p.touched_nets.end());records.push_back(record);
  }
 }
 auto selected() const{
  std::vector<std::uint32_t> order(records.size()),output(records.size());std::uint32_t status;
  auto count=select_identity(records.data(),records.size(),kinds.data(),kinds.size(),identity_units.data(),identity_units.size(),members.data(),members.size(),trials.data(),trials.size(),sites.data(),sites.size(),nets.data(),nets.size(),units.data(),units.size(),order.data(),order.size(),output.data(),output.size(),status);
  if(status)throw std::runtime_error("encoded transaction validation failed");
  std::vector<tileplace_snapshot::Proposal> result;for(unsigned i=0;i<count;++i)result.push_back(proposals.at(output[i]));return result;
 }
};
}
