#include "tileplace.hpp"
#include <iostream>
using namespace tileplace;
int main() {
    static Instance in[MAX_INSTANCES]{}; static Page pages[MAX_PAGES]{};
    static std::uint16_t a[MAX_INSTANCES]{}, x[MAX_INSTANCES]{}, y[MAX_INSTANCES]{};
    pages[0] = {0,0,7,7,{4,1,1},{0,0,0}}; pages[1] = {8,0,15,7,{4,1,1},{0,0,0}};
    for (int i=0;i<8;++i) in[i] = {static_cast<std::uint16_t>(i*2),2,0,static_cast<std::uint16_t>(1000+i*500),0,0,15,7,0};
    in[6].resource_type=1; in[7].resource_type=2;
    PlacementMetrics m{}; tileplace_kernel(in,pages,a,x,y,8,2,&m);
    if(m.placed!=8||m.unplaced!=0) return 1;
    for(int i=0;i<8;++i) if(a[i]>1||x[i]>15||y[i]>7) return 2;
    std::cout<<"tileplace_tb: PASS\n"; return 0;
}
