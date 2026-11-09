#include "eligible_words.hpp"
#include <random>
#include <vector>
#include <set>
#include <iostream>
int main(){std::mt19937 rng(131);auto floor=[](int x,int d){return x>=0?x/d:-int((-std::int64_t(x)+d-1)/d);};
 for(unsigned t=0;t<3000;++t){std::uint64_t blocks[128]{},positions[32],units[32]{};unsigned members[16],out[8];std::set<unsigned> focus;std::vector<unsigned> fw,expected;int width=1+rng()%11,height=1+rng()%11;unsigned color=t%4;
 for(unsigned i=0;i<16;++i){blocks[8*i]=3*i+2;members[i]=3*i+2;tileplace_hbm::Location p{int(rng()%101)-50,int(rng()%101)-50,int(i%3),int(i%2)};if(t%31==0&&i==0)p.x=INT32_MIN;tileplace_wire_candidates::store(positions+2*i,p);if(t%3&&rng()%3==0)focus.insert(members[i]);}
 fw.assign(focus.begin(),focus.end());for(unsigned i=0;i<8;++i){units[4*i]=2*i;units[4*i+1]=2;units[4*i+2]=i%2;bool focused=focus.empty()||focus.count(members[2*i])||focus.count(members[2*i+1]);auto p=tileplace_wire_candidates::location(positions+4*i);unsigned c=(unsigned(floor(p.x,width))&1)*2+(unsigned(floor(p.y,height))&1);if(focused&&c==color)expected.push_back(i);}
 unsigned status;auto n=tileplace_wire_control::eligible(units,8,members,16,fw.data(),fw.size(),blocks,positions,16,width,height,color,out,8,status);if(status||n!=expected.size())return 1;for(unsigned i=0;i<n;++i)if(out[i]!=expected[i])return 2;
 if(n){for(auto &x:out)x=99;auto m=tileplace_wire_control::eligible(units,8,members,16,fw.data(),fw.size(),blocks,positions,16,width,height,color,out,n-1,status);if(m||status!=4)return 3;for(auto x:out)if(x!=99)return 4;}
 }
 unsigned status,out=99;std::uint64_t units[4]={0,0,0,0};auto n=tileplace_wire_control::eligible(units,1,nullptr,0,nullptr,0,nullptr,nullptr,0,1,1,0,&out,1,status);if(n||status!=2||out!=99)return 5;
 std::uint64_t block[8]={2},pos[2]{},u[4]={0,1,0,0};unsigned member=2;
 auto check=[&](std::uint64_t uc,std::uint64_t bc,int width,unsigned color,unsigned expected){out=99;auto n=tileplace_wire_control::eligible(u,uc,&member,1,nullptr,0,block,pos,bc,width,1,color,&out,1,status);return !n&&status==expected&&out==99;};
 if(!check(1,1,0,0,1)||!check(1,1,1,4,1))return 6;
 u[0]=UINT64_MAX;if(!check(1,1,1,0,2))return 7;u[0]=0;member=999;if(!check(1,1,1,0,3))return 8;member=2;
 if(!check(UINT64_MAX,1,1,0,5)||!check(1,UINT64_MAX,1,0,5))return 9;
 std::cout<<"3000 focus/color eligible sets and atomic capacity/empty/dimensions/color/CSR/unknown/scaling faults pass\n";
}
