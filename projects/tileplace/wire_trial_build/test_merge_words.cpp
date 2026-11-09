#include "merge_words.hpp"
#include <random>
#include <map>
#include <array>
#include <vector>
#include <iostream>
int main(){std::mt19937 rng(151);for(unsigned t=0;t<3000;++t){std::map<unsigned,std::array<std::uint64_t,2>> a,b;for(unsigned i=0;i<t%17;++i){a[rng()%30]={rng(),rng()};b[rng()%30]={rng(),rng()};}auto expected=a;expected.insert(b.begin(),b.end());std::vector<std::uint64_t> aw,bw,out(3*(a.size()+b.size()),99);for(auto [id,p]:a)aw.insert(aw.end(),{id,p[0],p[1]});for(auto [id,p]:b)bw.insert(bw.end(),{id,p[0],p[1]});unsigned status;auto n=tileplace_wire_trial_build::merge(aw.data(),a.size(),bw.data(),b.size(),out.data(),a.size()+b.size(),status);if(status||n!=expected.size())return 1;unsigned i=0;for(auto [id,p]:expected){if(out[3*i]!=id||out[3*i+1]!=p[0]||out[3*i+2]!=p[1])return 2;++i;}if(n){std::fill(out.begin(),out.end(),99);if(tileplace_wire_trial_build::merge(aw.data(),a.size(),bw.data(),b.size(),out.data(),n-1,status)||status!=2)return 3;for(auto w:out)if(w!=99)return 4;}}
 std::uint64_t bad[6]={5,0,0,2,0,0},out[6]={99,99,99,99,99,99};unsigned status;if(tileplace_wire_trial_build::merge(bad,2,nullptr,0,out,2,status)||status!=1)return 5;for(auto w:out)if(w!=99)return 6;std::cout<<"3000 sorted trial merge cases and atomic capacity/order faults pass\n";}
