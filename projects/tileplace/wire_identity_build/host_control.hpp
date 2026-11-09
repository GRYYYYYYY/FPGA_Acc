#pragma once
#include "batch_words.hpp"
#include "../wire_dedup/dedup_words.hpp"
#include "../cpp_snapshot/transactions.hpp"
#include <optional>
namespace tileplace_wire_identity_build {
// Transitional container packing only; kind strings, unit sorting and six-word
// candidate identities are constructed by the integer batch data plane.
struct Packed {
 std::vector<tileplace_snapshot::Proposal> proposals;
 std::vector<std::uint64_t> records,units,trials;
 std::vector<std::uint32_t> members;
 std::vector<std::uint8_t> kinds;
 explicit Packed(std::vector<tileplace_snapshot::Proposal> input):proposals(std::move(input)){
  if(proposals.size()>UINT32_MAX/10)throw std::length_error("identity batch too large");
  std::map<tileplace_snapshot::Unit,std::uint32_t> registry;
  for(const auto& p:proposals)for(const auto& u:p.units)registry.emplace(u,0);
  std::vector<std::uint64_t> source_units,source_trials,descriptors;
  std::vector<std::uint32_t> owners;std::uint32_t index=0;
  for(auto& e:registry){e.second=index++;source_units.insert(source_units.end(),{members.size(),e.first.size(),0,0});members.insert(members.end(),e.first.begin(),e.first.end());}
  const std::string names[5]={"move","swap","macro_swap","chain2","chain3"};
  for(const auto& p:proposals){unsigned kind=0;while(kind<5&&names[kind]!=p.kind)++kind;
   descriptors.insert(descriptors.end(),{std::uint64_t(p.score),kind,owners.size(),p.units.size(),source_trials.size()/3,p.trial.size()});
   for(const auto& u:p.units)owners.push_back(registry.at(u));
   for(const auto& t:p.trial){const auto& point=t.second;source_trials.insert(source_trials.end(),{t.first,std::uint32_t(point.x)|(std::uint64_t(std::uint32_t(point.y))<<32),std::uint32_t(point.subtile)|(std::uint64_t(std::uint32_t(point.layer))<<32)});}
  }
  if(source_trials.size()/3>UINT32_MAX)throw std::length_error("identity trial pool too large");
  records.resize(7*proposals.size());kinds.resize(10*proposals.size());units.resize(6*proposals.size());trials.resize(source_trials.size());
  if(proposals.empty())return;
  auto r=encode(descriptors.data(),proposals.size(),owners.data(),owners.size(),source_units.data(),registry.size(),members.data(),members.size(),source_trials.data(),source_trials.size()/3,records.data(),proposals.size(),kinds.data(),kinds.size(),units.data(),units.size()/2,trials.data(),trials.size()/3);
  if(r.status)throw std::invalid_argument("batch identity rejected: "+std::to_string(r.status));
  kinds.resize(r.kinds);units.resize(2*r.units);trials.resize(3*r.trials);
 }
};
template<class Identity>
inline std::optional<tileplace_snapshot::Proposal> choose(std::vector<tileplace_snapshot::Proposal> input,const std::set<Identity>& forbidden){
 if(input.size()>UINT32_MAX||forbidden.size()>UINT32_MAX)throw std::length_error("candidate count overflow");
 auto count=std::uint32_t(input.size());
 for(const auto& id:forbidden){tileplace_snapshot::Proposal p;p.kind=std::get<0>(id);p.units=std::get<1>(id);p.trial=std::get<2>(id);input.push_back(std::move(p));}
 Packed encoded(std::move(input));std::vector<std::uint64_t> blocked;
 for(std::size_t i=count;i<encoded.proposals.size();++i){auto c=encoded.records.data()+7*i;blocked.insert(blocked.end(),c+1,c+7);}
 std::uint64_t group[2]={0,count};std::uint32_t index=UINT32_MAX,status;
 tileplace_wire_best::best(encoded.records.data(),count,group,1,blocked.data(),forbidden.size(),encoded.kinds.data(),encoded.kinds.size(),encoded.units.data(),encoded.units.size()/2,encoded.members.data(),encoded.members.size(),encoded.trials.data(),encoded.trials.size()/3,&index,1,status);
 if(status)throw std::invalid_argument("batch best rejected");
 if(index==UINT32_MAX)return std::nullopt;
 return std::move(encoded.proposals.at(index));
}
inline std::vector<tileplace_snapshot::Proposal> unique(std::vector<tileplace_snapshot::Proposal> input){
 Packed encoded(std::move(input));std::vector<std::uint32_t> indices(encoded.proposals.size());unsigned status;
 auto n=tileplace_wire_dedup::dedup(encoded.records.data(),encoded.proposals.size(),encoded.kinds.data(),encoded.kinds.size(),encoded.units.data(),encoded.units.size()/2,encoded.members.data(),encoded.members.size(),encoded.trials.data(),encoded.trials.size()/3,indices.data(),indices.size(),status);
 if(status)throw std::invalid_argument("batch dedup rejected");
 std::vector<tileplace_snapshot::Proposal> result;for(unsigned i=0;i<n;++i)result.push_back(std::move(encoded.proposals.at(indices[i])));return result;
}
}
