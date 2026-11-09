#include "trial_words.hpp"
#include "../hbm_abi/trial_legality_array.hpp"
#include <random>
#include <vector>
#include <iostream>
std::uint64_t pair(int a,int b){return std::uint32_t(a)|(std::uint64_t(std::uint32_t(b))<<32);}
int main(){using namespace tileplace_hbm;std::mt19937 rng(92);unsigned legal=0;
 for(unsigned q=0;q<5000;++q){Block blocks[3]{};Location positions[3]{};Region regions[3]{};std::vector<Site> sites;std::vector<std::uint64_t> bw,pw,rw,sw,mw;std::vector<TrialMove> moves;
  for(unsigned i=0;i<3;++i){blocks[i].id=3+7*i;blocks[i].type_id=1;blocks[i].regions={i,1};blocks[i].fixed_mask=(q%3==0?0x80000000u:0)|(q%7==0?2:0);positions[i]={int(i),0,0,0};regions[i]={0,0,2,1,0,0,-1,0};auto b=blocks[i];bw.insert(bw.end(),{pair(b.id,b.type_id),0,0,i,1,0,0,b.fixed_mask});pw.insert(pw.end(),{pair(i,0),0});rw.insert(rw.end(),{0,pair(2,1),0,pair(-1,0)});}
  for(int x=0;x<4;++x)for(int y=0;y<3;++y){sites.push_back({{x,y,0,0},1,{0,0,0}});sw.insert(sw.end(),{pair(x,y),0,1,0});}
  for(unsigned i=0;i<q%4;++i){auto id=blocks[i].id;if(q%11==0)id=11;Location p{int(rng()%6)-1,int(rng()%4)-1,0,0};moves.push_back({id,p});mw.insert(mw.end(),{id,pair(p.x,p.y),0});}
  std::uint32_t a=0,b=0;auto expected=trial_legality_array(blocks,positions,3,sites.data(),sites.size(),regions,3,moves.data(),moves.size(),a);auto actual=tileplace_wire_legality::trial(bw.data(),pw.data(),3,sw.data(),sites.size(),rw.data(),3,mw.data(),moves.size(),b);if(a!=b||expected!=actual)return 1;legal+=actual;
 }
 unsigned extremes=0,rejections=0;
 for(unsigned dimension=0;dimension<4;++dimension)for(int limit:{INT32_MIN,INT32_MAX}){
  Location target{};int values[4]{};values[dimension]=limit;target={values[0],values[1],values[2],values[3]};
  Block block{};block.id=3;block.type_id=1;block.fixed_mask=0x8000000f;block.regions={0,1};for(unsigned k=0;k<4;++k)block.fixed[k]=values[k];
  Location current{};Site site{target,1,{0,0,0}};Region region{INT32_MIN,INT32_MIN,INT32_MAX,INT32_MAX,INT32_MIN,INT32_MAX,-1,0};TrialMove move{3,target};
  auto compare=[&](bool expect){std::uint64_t bw[8]={pair(3,1),0,0,0,1,pair(block.fixed[0],block.fixed[1]),pair(block.fixed[2],block.fixed[3]),block.fixed_mask},pw[2]{},sw[4]={pair(target.x,target.y),pair(target.subtile,target.layer),1,0},rw[4]={pair(INT32_MIN,INT32_MIN),pair(INT32_MAX,INT32_MAX),pair(INT32_MIN,INT32_MAX),pair(-1,0)},mw[3]={3,pair(target.x,target.y),pair(target.subtile,target.layer)};
   unsigned a=0,b=0;auto typed=trial_legality_array(&block,&current,1,&site,1,&region,1,&move,1,a);auto wire=tileplace_wire_legality::trial(bw,pw,1,sw,1,rw,1,mw,1,b);return a==b&&typed==wire&&wire==expect;
  };
  if(!compare(true))return 2;
  ++extremes;
  for(unsigned k=0;k<4;++k){auto saved=block.fixed[k];block.fixed[k]=saved==INT32_MAX?INT32_MIN:INT32_MAX;if(!compare(false))return 3;++rejections;block.fixed[k]=saved;}
 }
 std::uint64_t bw[8]={pair(3,1),0,0,0,0,0,0,0},pw[2]{},sw[4]={pair(1,0),0,1,0},mw[6]={3,pair(1,0),0,3,pair(2,0),0};unsigned status=0;
 auto fault=[&](unsigned expected){auto result=tileplace_wire_legality::trial(bw,pw,1,sw,1,nullptr,0,mw,2,status);return !result&&status==expected;};
 if(!fault(1))return 4;
 mw[0]=11;if(!fault(1))return 5;mw[0]=3;bw[3]=UINT64_MAX;if(!fault(2))return 6;bw[3]=0;
 for(unsigned dimension=0;dimension<3;++dimension){auto result=tileplace_wire_legality::trial(nullptr,nullptr,dimension==0?UINT64_MAX:0,nullptr,dimension==1?UINT64_MAX:0,nullptr,dimension==2?UINT64_MAX:0,nullptr,0,status);if(result||status!=3)return 7;}
 std::cout<<extremes<<" four-dimensional extreme accepts, "<<rejections<<" fixed rejects and6 status errors pass\n";
 std::cout<<"5000 wire legality queries pass; legal="<<legal<<'\n';
}
