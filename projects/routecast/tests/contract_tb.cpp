#include "routecast.hpp"
#include <algorithm>
#include <iostream>
#include <limits>
#include <string>
using namespace routecast;
static Tile t[MAX_TILES];
static EdgeTemplate e[MAX_EDGES];
static DirtyConnection d[MAX_DIRTY];
static std::uint32_t q[MAX_EDGES];
static unsigned checks=0;
void require(bool value, const char* name) {
    ++checks;
    if(!value) { std::cerr << "FAIL: " << name << '\n'; std::exit(1); }
}
void reset() {
    std::fill_n(t,MAX_TILES,Tile{}); std::fill_n(e,MAX_EDGES,EdgeTemplate{});
    std::fill_n(d,MAX_DIRTY,DirtyConnection{}); std::fill_n(q,MAX_EDGES,0U);
    t[0]={0,1,0,0}; t[1]={1,1,1,0}; t[2]={2,0,2,0};
    e[0]={1,0,2,1,0}; e[1]={2,0,2,1,0}; d[0]={0,2,256,0};
}
SketchMetrics run(unsigned hops=4,unsigned connections=1,unsigned tiles=3,unsigned edges=2) {
    SketchMetrics m{}; routecast_kernel(t,e,d,q,tiles,edges,connections,hops,&m); return m;
}
int main() {
    reset(); auto m=run();
    require(m.completed==1 && m.failed==0 && m.updates==2 && q[0]==256 && q[1]==256,"complete path");
    reset(); m=run(1);
    require(m.failed==1 && m.updates==0 && q[0]==0 && q[1]==0,"hop truncation atomic");
    reset(); t[1].edge_count=0; m=run();
    require(m.failed==1 && q[0]==0,"dead end atomic");
    reset(); d[0].sink_tile=MAX_TILES; m=run();
    require(m.invalid_connections==1 && m.failed==1 && q[0]==0,"invalid sink");
    reset(); d[0].source_tile=MAX_TILES; m=run();
    require(m.invalid_connections==1 && q[0]==0,"invalid source");
    reset(); d[0].flags=1; m=run();
    require(m.invalid_connections==1 && q[0]==0,"unsupported flags");
    reset(); d[0].sink_tile=0; m=run(0);
    require(m.completed==1 && m.updates==0,"zero length success");
    reset(); m=run(0);
    require(m.failed==1 && q[0]==0,"zero hop failure");
    reset(); e[1].capacity=0; m=run();
    require(m.failed==1 && q[0]==0,"zero capacity excluded");
    reset(); q[1]=std::numeric_limits<unsigned>::max()-100; m=run();
    require(m.overflow_rejections==1 && m.failed==1 && q[0]==0 && q[1]==std::numeric_limits<unsigned>::max()-100,"overflow atomic");
    reset(); t[2].edge_begin=0xffffffffU; m=run();
    require(m.invalid_batch==1 && q[0]==0,"invalid unreachable CSR row");
    reset(); t[0].edge_count=3; m=run();
    require(m.invalid_batch==1 && q[0]==0,"CSR range overflow");
    reset(); e[1].dst=3; m=run();
    require(m.invalid_batch==1 && q[0]==0,"invalid graph destination");
    reset(); m=run(MAX_HOPS+1);
    require(m.invalid_batch==1 && q[0]==0,"hop bound");
    reset(); m=run(4,MAX_DIRTY+1);
    require(m.invalid_batch==1 && q[0]==0,"connection bound");
    reset(); m=run(4,1,MAX_TILES+1);
    require(m.invalid_batch==1,"tile bound");
    reset(); m=run(4,1,3,MAX_EDGES+1);
    require(m.invalid_batch==1,"edge bound");
    reset(); d[1]={0,3,256,0}; m=run(4,2);
    require(m.completed==1 && m.failed==1 && q[0]==256 && q[1]==256,"per connection commit");
    reset(); d[1]=d[0]; d[2]=d[0]; m=run(4,3);
    require(m.completed==3 && q[0]==768 && q[1]==768 && m.saturated==2 && m.max_demand_q==768,"Q8 capacity and event metrics");
    reset(); t[0].edge_count=2; t[1].edge_begin=2; e[1]=e[0]; e[2]={2,0,2,1,0};
    m=run(4,1,3,3);
    require(q[0]==256 && q[1]==0 && q[2]==256,"stable edge tie break");
    reset(); t[0].edge_count=2; t[1].edge_begin=2; e[1]=e[0]; e[2]={2,0,2,1,0}; q[0]=512;
    m=run(4,1,3,3);
    require(q[0]==512 && q[1]==256 && q[2]==256,"congestion alternative");
    reset(); t[1].x=0; m=run();
    require(m.failed==1 && q[0]==0,"same coordinate RR transition unsupported");
    reset(); q[0]=123; m=run(4,0);
    require(m.completed==0 && m.failed==0 && q[0]==123,"empty batch preserves state");
    std::cout << "routecast_contract_tb: PASS (" << checks << " checks)\n";
}
