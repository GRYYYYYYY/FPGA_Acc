#pragma once
#include "transaction_search.hpp"
namespace tileplace_hbm {
class WireTransactionFeedbackSearch {
 struct Version {
  std::vector<std::uint8_t> bytes;
  WireBestSearch search;
  explicit Version(const std::vector<std::uint8_t>& b):bytes(b),search(b){}
 };
 std::shared_ptr<const Version> current_;
 std::shared_ptr<const int> owner_=std::make_shared<const int>(0);
 static std::array<std::vector<std::uint8_t>,13> sections(const std::vector<std::uint8_t>& b){
  constexpr std::array<std::size_t,13> widths{64,16,32,32,48,4,16,32,4,32,16,16,4};
  std::array<std::vector<std::uint8_t>,13> out;std::size_t start=224;
  for(unsigned i=0;i<13;++i){std::uint64_t count=0;for(unsigned j=0;j<8;++j)count|=std::uint64_t(b.at(24+16*i+j))<<(8*j);
   auto end=start+count*widths[i];out[i]={b.begin()+start,b.begin()+end};start=end;}
  return out;
 }
public:
 struct Snapshot {private:friend class WireTransactionFeedbackSearch;std::shared_ptr<const Version> value;std::shared_ptr<const int> owner;};
 explicit WireTransactionFeedbackSearch(const std::vector<std::uint8_t>& b):current_(std::make_shared<const Version>(b)){}
 auto snapshot() const{Snapshot s;s.value=current_;s.owner=owner_;return s;}
 void restore(const Snapshot& s){if(!s.value||s.owner!=owner_)throw std::invalid_argument("foreign feedback snapshot");current_=s.value;}
 const auto& positions() const{return current_->search.positions();}
 void commit(const tileplace_snapshot::Positions& changes){auto next=std::make_shared<Version>(*current_);next->search.commit(changes);current_=next;}
 void feedback(const std::vector<std::uint8_t>& b){
  auto next=std::make_shared<Version>(b); // Validate and construct fully before publishing.
  if(next->search.positions()!=positions())throw std::invalid_argument("feedback placement differs");
  auto old=sections(current_->bytes),fresh=sections(b);
  for(unsigned i:{0u,2u,3u,4u,5u,6u,7u,8u})if(old[i]!=fresh[i])throw std::invalid_argument("feedback topology differs");
  current_=next;
 }
 auto proposals(unsigned selector,bool color,const tileplace_snapshot::CallbackProposalConfig& config,
  const std::set<tileplace_snapshot::ProposalIdentity>& forbidden={},
  const std::vector<tileplace_snapshot::CallbackGuard>& guards={},tileplace_snapshot::TransactionColorStats* stats=nullptr) const{
  return current_->search.proposals(selector,color,config,forbidden,guards,stats);
 }
};
}
