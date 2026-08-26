#include "routecast.hpp"
#include <iostream>
using namespace routecast;
int main(){ static Tile t[MAX_TILES]{}; static EdgeTemplate e[MAX_EDGES]{}; static DirtyConnection d[MAX_DIRTY]{}; static std::uint32_t q[MAX_EDGES]{};
 t[0]={0,1,0,0};t[1]={1,2,1,0};t[2]={3,1,2,0};e[0]={1,0,2,1,0};e[1]={0,0,2,0,0};e[2]={2,1,2,1,1};e[3]={1,1,2,0,1};d[0]={0,2,256,0};d[1]={0,2,256,0};SketchMetrics m{};
 routecast_kernel(t,e,d,q,3,4,2,4,&m);if(m.updates!=4||q[0]!=512||q[2]!=512||m.saturated!=0){std::cerr<<"updates="<<m.updates<<" q0="<<q[0]<<" q2="<<q[2]<<" sat="<<m.saturated<<"\n";return 1;}std::cout<<"routecast_tb: PASS\n";return 0;}
