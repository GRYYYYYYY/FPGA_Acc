#include "dieroute.hpp"
#include <iostream>
using namespace dieroute;
int main(){static Boundary b[MAX_BOUNDARIES]{};static CrossDieTask t[MAX_TASKS]{};static Allocation a[MAX_TASKS]{};static DieQueue q[MAX_DIES]{};b[0]={0,1,2,0,100,0,0};b[1]={0,1,3,0,200,0,0};t[0]={0,0,1,60000,1,0};t[1]={1,0,1,1000,1,1};t[2]={2,0,1,30000,1,2};Metrics m{};dieroute_kernel(b,t,a,q,2,3,2,&m);if(m.allocated!=3||m.rejected!=0||b[0].reserved+b[1].reserved!=3){std::cerr<<"allocated="<<m.allocated<<" rejected="<<m.rejected<<" reserved="<<b[0].reserved+b[1].reserved<<"\n";return 1;}std::cout<<"dieroute_tb: PASS\n";return 0;}
