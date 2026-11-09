#pragma once
#include "host_control.hpp"
#include "../wire_transactions/selection_words.hpp"
namespace tileplace_wire_identity_build {
// Pack only conflict metadata; reuse batch-built full identities in selection.
inline std::vector<tileplace_snapshot::Proposal> select(std::vector<tileplace_snapshot::Proposal> input){
 Packed encoded(std::move(input));
 std::vector<std::uint64_t> records,sites;
 std::vector<std::uint32_t> nets,conflict_units;
 std::map<tileplace_snapshot::Unit,std::uint32_t> registry;
 for(const auto& p:encoded.proposals)for(const auto& u:p.units)registry.emplace(u,0);
 std::uint32_t index=0;for(auto& e:registry)e.second=index++;
 for(std::size_t i=0;i<encoded.proposals.size();++i){const auto& p=encoded.proposals[i];auto c=encoded.records.data()+7*i;
  records.insert(records.end(),c,c+7);
  records.insert(records.end(),{sites.size()/2,p.write_sites.size(),nets.size(),p.touched_nets.size(),conflict_units.size(),p.units.size()});
  for(const auto& s:p.write_sites)sites.insert(sites.end(),{std::uint32_t(s.x)|(std::uint64_t(std::uint32_t(s.y))<<32),std::uint32_t(s.subtile)|(std::uint64_t(std::uint32_t(s.layer))<<32)});
  nets.insert(nets.end(),p.touched_nets.begin(),p.touched_nets.end());
  for(const auto& u:p.units)conflict_units.push_back(registry.at(u));
 }
 std::vector<std::uint32_t> order(encoded.proposals.size()),selected(encoded.proposals.size());unsigned status;
 auto count=tileplace_wire_transactions::select(records.data(),encoded.proposals.size(),encoded.kinds.data(),encoded.kinds.size(),encoded.units.data(),encoded.units.size()/2,encoded.members.data(),encoded.members.size(),encoded.trials.data(),encoded.trials.size()/3,sites.data(),sites.size()/2,nets.data(),nets.size(),conflict_units.data(),conflict_units.size(),order.data(),order.size(),selected.data(),selected.size(),status);
 if(status)throw std::invalid_argument("batch identity conflict selection rejected");
 std::vector<tileplace_snapshot::Proposal> result;for(unsigned i=0;i<count;++i)result.push_back(std::move(encoded.proposals.at(selected[i])));return result;
}
}
