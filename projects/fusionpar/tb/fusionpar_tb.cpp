#include "fusionpar.hpp"
#include <iostream>
using namespace fusionpar;
int main(){static Move m[MAX_MOVES]{};static AffectedConnection a[MAX_AFFECTED]{};static Resource s[MAX_RESOURCES]{};static MoveResult r[MAX_MOVES]{};s[2]={0,1,4};s[3]={1,1,7};m[0]={0,0,0,1,1,2,10,0,0,1,1};a[0]={5,2,4,1,100};m[1]={1,0,0,2,2,3,10,0,1,1,1};a[1]={6,3,7,1,100};Metrics x{};fusionpar_kernel(m,a,s,r,2,2,4,100,200,&x);if(x.committed!=1||x.conflicts!=1||r[0].status!=1||r[1].status!=3||x.repair_tasks!=1)return 1;std::cout<<"fusionpar_tb: PASS\n";return 0;}
