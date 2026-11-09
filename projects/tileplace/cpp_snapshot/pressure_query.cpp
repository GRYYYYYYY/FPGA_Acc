#include "pressure_snapshot.hpp"
#include <iostream>
int main() {
 unsigned n,q; if(!(std::cin>>n>>q)) return 1;
 std::vector<tileplace_snapshot::Edge> edges(n);
 for(auto& e:edges) std::cin>>e.x0>>e.y0>>e.x1>>e.y1>>e.weight;
 tileplace_snapshot::PressureSnapshot snapshot(edges);
 while(q--) {tileplace_snapshot::Point a,b; std::cin>>a.x>>a.y>>b.x>>b.y;
 std::cout<<snapshot.path(a,b,true)<<' '<<snapshot.path(a,b,false)<<' '<<snapshot.connection(a,b)<<'\n';}
}
