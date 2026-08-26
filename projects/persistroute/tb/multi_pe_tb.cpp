#include "multi_pe.hpp"
#include <iostream>
using namespace persistroute;
int main(){static Task t[MAX_TASKS]{};static PEAssignment a[MAX_TASKS]{};for(int i=0;i<16;++i)t[i]={static_cast<std::uint32_t>(i),static_cast<std::uint32_t>(i),static_cast<std::uint32_t>(i),static_cast<std::uint32_t>(i*17),0,0,0,0,0};SchedulerMetrics m{};multi_pe_schedule(t,a,16,4,4,&m);if(m.assigned!=16)return 1;for(int i=0;i<4;++i)if(m.pe_load[i]!=4)return 2;std::cout<<"multi_pe_tb: PASS\n";return 0;}
