#include "net_cost.hpp"
#include <iostream>
using namespace tileplace_snapshot;
int main() {
    unsigned cases; std::cin>>cases;
    while(cases--) {
        unsigned count, edges, nets, feedback; std::cin>>count>>edges>>nets>>feedback;
        Positions before,after; std::set<std::uint32_t> changed;
        for(unsigned id=0;id<count;++id) {
            Point a,b; unsigned flag; std::cin>>a.x>>a.y>>b.x>>b.y>>flag;
            before[id]=a; after[id]=b; if(flag) changed.insert(id);
        }
        std::vector<Edge> pressure(edges);
        for(auto& e:pressure) std::cin>>e.x0>>e.y0>>e.x1>>e.y1>>e.weight;
        std::vector<Net> touched(nets);
        for(auto& net:touched) {
            unsigned members,connections; std::cin>>members>>connections;
            net.members.resize(members); net.connections.resize(connections);
            for(auto& id:net.members) std::cin>>id;
            for(auto& c:net.connections) std::cin>>c.source>>c.sink>>c.weight;
        }
        std::vector<Connection> routed(feedback);
        for(auto& c:routed) std::cin>>c.source>>c.sink>>c.weight;
        auto result=cost_pair(touched,changed,before,after,routed,PressureSnapshot(pressure));
        for(auto value:result.first) std::cout<<value<<' ';
        for(auto value:result.second) std::cout<<value<<' ';
        std::cout<<'\n';
    }
}
