#pragma once
#include "dedup_words.hpp"
#include "../wire_transactions/encoder_words.hpp"
namespace tileplace_wire_dedup {
inline std::vector<tileplace_snapshot::Proposal> unique(std::vector<tileplace_snapshot::Proposal> input){
 tileplace_wire_transactions::Encoded encoded(std::move(input));std::vector<std::uint64_t> records;
 for(std::size_t i=0;i<encoded.proposals.size();++i){auto p=encoded.rw.data()+13*i;records.insert(records.end(),p,p+7);}
 std::vector<std::uint32_t> indices(encoded.proposals.size());std::uint32_t status;
 auto n=dedup(records.data(),encoded.proposals.size(),encoded.kinds.data(),encoded.kinds.size(),encoded.iw.data(),encoded.identity_units.size(),encoded.members.data(),encoded.members.size(),encoded.tw.data(),encoded.trials.size(),indices.data(),indices.size(),status);
 if(status)throw std::invalid_argument("wire dedup input rejected");
 std::vector<tileplace_snapshot::Proposal> result;for(unsigned i=0;i<n;++i)result.push_back(std::move(encoded.proposals.at(indices[i])));return result;
}
}
