#pragma once
#include "best_words.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include <optional>
namespace tileplace_wire_best {
// Transitional host packing. Forbidden and candidate identities share one exact pool.
template<class Identity>
inline std::optional<tileplace_snapshot::Proposal> choose(std::vector<tileplace_snapshot::Proposal> candidates,const std::set<Identity>& forbidden){
 if(candidates.size()>UINT32_MAX||forbidden.size()>UINT32_MAX)throw std::length_error("best candidate count overflow");
 auto count=std::uint32_t(candidates.size());
 for(const auto& id:forbidden){tileplace_snapshot::Proposal p;p.kind=std::get<0>(id);p.units=std::get<1>(id);p.trial=std::get<2>(id);candidates.push_back(std::move(p));}
 tileplace_wire_transactions::Encoded encoded(std::move(candidates));std::vector<std::uint64_t> records,blocked;
 for(unsigned i=0;i<count;++i){auto r=encoded.rw.data()+13ULL*i;records.insert(records.end(),r,r+7);}
 for(std::size_t i=count;i<encoded.proposals.size();++i){auto r=encoded.rw.data()+13ULL*i;blocked.insert(blocked.end(),r+1,r+7);}
 std::uint64_t group[2]={0,count};std::uint32_t index=UINT32_MAX,status;
 best(records.data(),count,group,1,blocked.data(),forbidden.size(),encoded.kinds.data(),encoded.kinds.size(),encoded.iw.data(),encoded.identity_units.size(),encoded.members.data(),encoded.members.size(),encoded.tw.data(),encoded.trials.size(),&index,1,status);
 if(status)throw std::invalid_argument("best candidate wire input rejected");
 if(index==UINT32_MAX)return std::nullopt;
 return std::move(encoded.proposals.at(index));
}
}
