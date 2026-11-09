#include "root_words.hpp"
#include <random>
#include <vector>
#include <set>
#include <array>
#include <iostream>
int main(){std::mt19937 rng(91);using namespace tileplace_hbm;
 for(unsigned t=0;t<3000;++t){std::vector<Site> sites;std::set<std::array<int,4>> seen;unsigned count=rng()%100;
 for(unsigned i=0;i<count;++i){Location p{int(rng()%101)-50,int(rng()%101)-50,int(rng()%3),int(rng()%3)-1};if(seen.insert({p.x,p.y,p.subtile,p.layer}).second)sites.push_back({p,rng()%3,{0,0,0}});}
 Location src{int(rng()%101)-50,int(rng()%101)-50,int(rng()%3),int(rng()%3)-1};if(t%20==0)src.x=INT32_MIN;if(t%21==0)src.y=INT32_MAX;
 std::vector<std::uint64_t> words(sites.size()*4);for(unsigned i=0;i<sites.size();++i){tileplace_wire_candidates::store(words.data()+4*i,sites[i].location);words[4*i+2]=sites[i].type_id;}
 std::uint64_t sw[2],out[64]{};tileplace_wire_candidates::store(sw,src);Location expected[32]{};unsigned a,b,type=rng()%3,limit=rng()%33;int width=1+rng()%17,height=1+rng()%17;
 auto n=candidate_root_array(sites.data(),sites.size(),src,type,width,height,limit,expected,32,a);auto m=tileplace_wire_candidates::roots(words.data(),sites.size(),sw,type,width,height,limit,out,32,b);if(a!=b||n!=m)return 1;
 for(unsigned i=0;i<n;++i){auto p=tileplace_wire_candidates::location(out+2*i),q=expected[i];if(p.x!=q.x||p.y!=q.y||p.subtile!=q.subtile||p.layer!=q.layer)return 2;}
 }
 std::uint64_t out[2]={99,99},src[2]{};unsigned st;auto check=[&](std::uint64_t count,int width,unsigned limit,unsigned capacity,unsigned status){auto n=tileplace_wire_candidates::roots(nullptr,count,src,0,width,1,limit,out,capacity,st);return !n&&st==status&&out[0]==99&&out[1]==99;};
 if(!check(0,0,1,1,1)||!check(0,1,2,1,2)||!check(UINT64_MAX,1,1,1,3))return 3;
 std::cout<<"3000 root word differential cases and 3 atomic errors pass\n";
}
