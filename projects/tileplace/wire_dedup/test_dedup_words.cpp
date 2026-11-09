#include "dedup_words.hpp"
#include "../wire_transactions/encoder_words.hpp"
#include <random>
#include <iostream>
int main(){std::mt19937 rng(139);using Identity=std::tuple<std::string,std::vector<tileplace_snapshot::Unit>,tileplace_snapshot::Positions>;
 for(unsigned t=0;t<1000;++t){std::vector<tileplace_snapshot::Proposal> input;unsigned count=t%65;
 for(unsigned i=0;i<count;++i){tileplace_snapshot::Proposal p;if(i&&rng()%3==0)p=input[rng()%i];else{p.kind=i%2?"swap":"move";p.units={{i%7},{i%5}};p.trial[i%9]={int(rng()%11)-5,int(rng()%11)-5,int(rng()%5)-2,int(rng()%5)-2};}p.score=int(rng()%15)-10;input.push_back(p);}
 tileplace_wire_transactions::Encoded e(input);std::vector<std::uint64_t> words;std::map<Identity,unsigned> expected;
 for(unsigned i=0;i<count;++i){auto r=e.rw.data()+13ULL*i;words.insert(words.end(),r,r+7);Identity id=e.proposals[i].identity();auto old=expected.find(id);if(old==expected.end()||e.proposals[i].score<e.proposals[old->second].score)expected[id]=i;}
 std::vector<unsigned> out(count);unsigned status;auto n=tileplace_wire_dedup::dedup(words.data(),count,e.kinds.data(),e.kinds.size(),e.iw.data(),e.identity_units.size(),e.members.data(),e.members.size(),e.tw.data(),e.trials.size(),out.data(),out.size(),status);if(status||n!=expected.size())return 1;unsigned j=0;for(auto [id,index]:expected)if(out[j++]!=index)return 2;
 if(count){std::fill(out.begin(),out.end(),99);if(tileplace_wire_dedup::dedup(words.data(),count,e.kinds.data(),e.kinds.size(),e.iw.data(),e.identity_units.size(),e.members.data(),e.members.size(),e.tw.data(),e.trials.size(),out.data(),count-1,status)||status!=2)return 3;for(auto x:out)if(x!=99)return 4;}
 }
 unsigned out=99,status;std::uint64_t bad[7]={0,UINT64_MAX,1,0,0,0,0};if(tileplace_wire_dedup::dedup(bad,1,nullptr,0,nullptr,0,nullptr,0,nullptr,0,&out,1,status)||status!=3||out!=99)return 5;
 std::cout<<"1000 full-identity dedup sets and atomic capacity/identity faults pass\n";
}
