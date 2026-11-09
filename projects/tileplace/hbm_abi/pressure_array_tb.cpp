#include "pressure_array_core.hpp"
#include <iostream>
#include <vector>
int main(){unsigned n,m,q;std::cin>>n>>m>>q;std::vector<tileplace_hbm::PrefixLine> lines(n);std::vector<tileplace_hbm::PrefixEntry> entries(m);std::vector<tileplace_hbm::PressureQuery> queries(q);std::vector<tileplace_hbm::PressureResult> results(q);
 for(auto& r:lines)std::cin>>r.axis>>r.line>>r.total_pressure>>r.entries.offset>>r.entries.count;
 for(auto& r:entries)std::cin>>r.coordinate>>r.reserved>>r.cumulative_before;
 for(auto& r:queries)std::cin>>r.source.x>>r.source.y>>r.target.x>>r.target.y;
 tileplace_hbm::tileplace_pressure_array(lines.data(),entries.data(),queries.data(),results.data(),n,m,q);
 for(auto r:results)std::cout<<r.horizontal<<' '<<r.vertical<<' '<<r.minimum<<' '<<r.status<<'\n';}
