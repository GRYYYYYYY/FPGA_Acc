#include "write_sites_words.hpp"
#include <random>
#include <set>
#include <array>
#include <iostream>
int main(){std::mt19937 rng(127);unsigned unchanged=0;
 for(unsigned t=0;t<3000;++t){std::uint64_t blocks[64]{},positions[16],moves[24]{},output[32];unsigned mc=t%9;std::set<std::array<int,4>> expected;bool changed=false;
 for(unsigned i=0;i<8;++i){blocks[8*i]=3*i+2;tileplace_hbm::Location p{int(i),int(rng()%7)-3,int(i%2),int(i%3)};tileplace_wire_candidates::store(positions+2*i,p);}
 for(unsigned i=0;i<mc;++i){auto p=tileplace_wire_candidates::location(positions+2*i);auto q=p;if(t%3){q.x=int(rng()%11)-5;q.y=int(rng()%11)-5;q.subtile=int(rng()%5)-2;q.layer=int(rng()%5)-2;}if(t%17==0)q.x=INT32_MIN;if(t%19==0)q.layer=INT32_MAX;moves[3*i]=3*i+2;tileplace_wire_candidates::store(moves+3*i+1,q);expected.insert({p.x,p.y,p.subtile,p.layer});expected.insert({q.x,q.y,q.subtile,q.layer});changed|=!tileplace_wire_checks::equal(p,q);}
 for(auto &x:output)x=99;auto r=tileplace_wire_pipeline::write_sites(blocks,positions,8,moves,mc,output,16);if(r.status||r.count!=expected.size()||bool(r.changed)!=changed)return 1;unsigned i=0;for(auto e:expected){auto p=tileplace_wire_candidates::location(output+2*i++);if(std::array<int,4>{p.x,p.y,p.subtile,p.layer}!=e)return 2;}unchanged+=!changed;
 if(!expected.empty()){for(auto &x:output)x=99;r=tileplace_wire_pipeline::write_sites(blocks,positions,8,moves,mc,output,expected.size()-1);if(r.status!=2||r.count||r.changed)return 3;for(auto x:output)if(x!=99)return 4;}
 }
 std::uint64_t blocks[8]{},positions[2]{},moves[6]{},out[4]={99,99,99,99};blocks[0]=2;moves[0]=999;auto r=tileplace_wire_pipeline::write_sites(blocks,positions,1,moves,1,out,2);if(r.status!=1)return 5;moves[0]=moves[3]=2;r=tileplace_wire_pipeline::write_sites(blocks,positions,1,moves,2,out,2);if(r.status!=4)return 6;r=tileplace_wire_pipeline::write_sites(nullptr,nullptr,UINT64_MAX,nullptr,0,out,2);if(r.status!=3)return 7;for(auto x:out)if(x!=99)return 8;
 std::cout<<"3000 write-site unions pass; unchanged="<<unchanged<<"; atomic capacity/ID/duplicate/scaling faults pass\n";
}
