#include "best_words.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include <random>
#include <iostream>
int main(){std::mt19937 rng(137);
 for(unsigned t=0;t<1000;++t){std::vector<tileplace_snapshot::Proposal> proposals;unsigned count=t%40;for(unsigned i=0;i<count;++i){tileplace_snapshot::Proposal p;p.kind=i%2?"swap":"move";p.score=int(rng()%12)-9;p.units={{unsigned(rng()%8),unsigned(rng()%8)},{unsigned(rng()%8)}};p.trial[i+20]={int(rng()%11)-5,int(rng()%11)-5,int(rng()%7)-3,int(rng()%7)-3};proposals.push_back(p);}
 tileplace_wire_transactions::Encoded e(proposals);std::vector<std::uint64_t> candidates,forbidden;std::set<std::tuple<std::string,std::vector<tileplace_snapshot::Unit>,tileplace_snapshot::Positions>> blocked;for(unsigned i=0;i<count;++i){auto r=e.rw.data()+13*i;candidates.insert(candidates.end(),r,r+7);if(i%7==t%7){forbidden.insert(forbidden.end(),r+1,r+7);blocked.insert(e.proposals[i].identity());}}
 std::uint64_t groups[4]={0,count/2,count/2,count-count/2};unsigned out[2],status;auto n=tileplace_wire_best::best(candidates.data(),count,groups,2,forbidden.data(),forbidden.size()/6,e.kinds.data(),e.kinds.size(),e.iw.data(),e.identity_units.size(),e.members.data(),e.members.size(),e.tw.data(),e.trials.size(),out,2,status);if(status)return 1;unsigned found=0;
 for(unsigned g=0;g<2;++g){unsigned expected=UINT32_MAX;for(unsigned j=0;j<groups[2*g+1];++j){unsigned i=groups[2*g]+j;auto &p=e.proposals[i];if(p.score>=0||blocked.count(p.identity()))continue;if(expected==UINT32_MAX||p.score<e.proposals[expected].score||(p.score==e.proposals[expected].score&&p.identity()<e.proposals[expected].identity()))expected=i;}if(out[g]!=expected)return 2;found+=expected!=UINT32_MAX;}if(n!=found)return 3;
 }
 unsigned out=99,status;std::uint64_t group[2]={UINT64_MAX,1};if(tileplace_wire_best::best(nullptr,0,group,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&out,1,status)||status!=1||out!=99)return 4;
 std::cout<<"1000 per-group full-identity best/forbidden cases and atomic group fault pass\n";
}
