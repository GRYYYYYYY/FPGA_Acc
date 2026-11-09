#pragma once
#include "selection_words.hpp"
#include "../array_transactions/encoder.hpp"
namespace tileplace_wire_transactions {
// Host encoding still uses containers. The selection data plane reads words.
struct Encoded:tileplace_transaction_array::Encoded {
 std::vector<std::uint64_t> rw,iw,tw,sw;
 explicit Encoded(std::vector<tileplace_snapshot::Proposal> input):tileplace_transaction_array::Encoded(std::move(input)){
  for(auto r:records)rw.insert(rw.end(),{std::uint64_t(r.score),r.identity.kind.offset,r.identity.kind.count,r.identity.units.offset,r.identity.units.count,r.identity.trial.offset,r.identity.trial.count,r.sites.offset,r.sites.count,r.nets.offset,r.nets.count,r.units.offset,r.units.count});
  for(auto u:identity_units)iw.insert(iw.end(),{u.offset,u.count});
  auto pack=[](int a,int b){return std::uint32_t(a)|(std::uint64_t(std::uint32_t(b))<<32);};
  for(auto t:trials){auto p=t.target;tw.insert(tw.end(),{t.id,pack(p.x,p.y),pack(p.subtile,p.layer)});}
  for(auto p:sites)sw.insert(sw.end(),{pack(p.x,p.y),pack(p.subtile,p.layer)});
 }
 auto selected() const{
  std::vector<std::uint32_t> order(records.size()),output(records.size());std::uint32_t status=0;
  auto count=select(rw.data(),records.size(),kinds.data(),kinds.size(),iw.data(),identity_units.size(),members.data(),members.size(),tw.data(),trials.size(),sw.data(),sites.size(),nets.data(),nets.size(),units.data(),units.size(),order.data(),order.size(),output.data(),output.size(),status);
  if(status)throw std::runtime_error("wire transaction validation failed");
  std::vector<tileplace_snapshot::Proposal> result;for(unsigned i=0;i<count;++i)result.push_back(proposals.at(output[i]));return result;
 }
};
}
