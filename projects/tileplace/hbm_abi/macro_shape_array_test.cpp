#include "macro_shape_array.hpp"
#include <algorithm>
#include <array>
#include <tuple>
#include <vector>
#include <random>
#include <iostream>
int main(){
 using namespace tileplace_hbm;std::mt19937 rng(36);unsigned equal=0,different=0;
 for(unsigned test=0;test<2000;++test){unsigned n=1+test%12;std::vector<Block> blocks(2*n);std::vector<Location> p(2*n);std::vector<unsigned>a(n),b(n);
  for(unsigned i=0;i<2*n;++i){blocks[i].id=i*11+3;blocks[i].type_id=i%n%3;}
  for(unsigned i=0;i<n;++i){a[i]=blocks[i].id;b[i]=blocks[i+n].id;p[i]={int(i)*3,int(rng()%31)-15,int(rng()%5)-2,int(rng()%5)-2};p[i+n]={p[i].x+100,p[i].y-50,p[i].subtile+10,p[i].layer-3};}
  if(test%3==0)++blocks[n].type_id;
  if(test%3==1&&n>1)++p[n+1].layer;
  using Item=std::tuple<unsigned,std::array<std::int64_t,4>>;
  auto shape=[&](unsigned start){std::vector<Item> out;auto root=p[start];for(unsigned i=0;i<n;++i){auto q=p[start+i];out.push_back({blocks[start+i].type_id,{std::int64_t(q.x)-root.x,std::int64_t(q.y)-root.y,std::int64_t(q.subtile)-root.subtile,std::int64_t(q.layer)-root.layer}});}std::sort(out.begin(),out.end());return out;};
  bool expected=shape(0)==shape(n);unsigned status;
  std::shuffle(b.begin()+1,b.end(),rng);
  bool actual=macro_shape_array(blocks.data(),p.data(),blocks.size(),a.data(),n,b.data(),n,status);
  if(status||actual!=expected)return 1;
  actual?++equal:++different;
 }
 Block blocks[2]{};blocks[0].id=3;blocks[1].id=7;Location p[2]{};unsigned a[1]={3},b[1]={999},status;
 if(macro_shape_array(blocks,p,2,a,0,a,1,status)||status!=1)return 2;
 if(macro_shape_array(blocks,p,2,a,1,b,1,status)||status!=2)return 3;
 Block extreme_blocks[4]{};for(unsigned i=0;i<4;++i)extreme_blocks[i].id=i;
 Location extremes[4]={{INT32_MIN,0,0,0},{INT32_MAX,1,0,0},{INT32_MIN,2,0,0},{INT32_MAX,3,0,0}};
 unsigned left[2]={0,1},right[2]={2,3};
 if(!macro_shape_array(extreme_blocks,extremes,4,left,2,right,2,status)||status)return 4;
 extremes[3].layer=1;if(macro_shape_array(extreme_blocks,extremes,4,left,2,right,2,status)||status)return 5;
 if(!equal||!different)return 6;
 std::cout<<"2000 shapes: "<<equal<<" equal, "<<different<<" different; 2 faults and 2 extremes pass\n";
}
