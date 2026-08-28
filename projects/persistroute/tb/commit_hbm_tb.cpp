#include "persistroute.hpp"
#include <cassert>
#include <iostream>
#include <vector>
using namespace persistroute;
int main(){
 std::vector<Resource> resources(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU});
 std::vector<Task> tasks(MAX_TASKS);tasks[0]={1,10,0,2,0,8,0,0,0};tasks[1]={2,11,0,2,0,8,1,0,0};
 std::vector<std::uint32_t> paths(MAX_TX_ENTRIES);paths[0]=1;paths[1]=2;paths[2]=1;paths[3]=2;
 std::vector<ReadEntry> reads(MAX_TX_ENTRIES);reads[0]={1,0};reads[1]={2,0};reads[2]={1,0};reads[3]={2,0};
 std::vector<PathResult> results(MAX_TASKS);results[0]={0,2,1,0,2,0};results[1]={2,2,1,2,2,0};Metrics metrics{};
 commit_hbm_kernel(resources.data(),resources.data(),resources.data(),resources.data(),tasks.data(),paths.data(),reads.data(),results.data(),3,2,4,0,&metrics);
 assert(results[0].status==4&&results[1].status==2&&metrics.commits==1&&metrics.conflicts==1);
 std::vector<Resource> shared(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU});tasks[0]={3,20,0,2,0,8,0,0,0};tasks[1]={4,20,0,2,0,8,1,0,0};results[0]={0,2,1,0,2,0};results[1]={2,2,1,2,2,0};metrics={};
 commit_hbm_kernel(shared.data(),shared.data(),shared.data(),shared.data(),tasks.data(),paths.data(),reads.data(),results.data(),3,2,4,0,&metrics);
 assert(results[0].status==4&&results[1].status==4&&shared[1].occupancy==1&&shared[2].occupancy==1);
 std::vector<Resource> negotiated(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU});
 tasks[0]={5,30,0,2,0,8,0,0,0};tasks[1]={6,31,0,2,0,8,1,0,0};
 results[0]={0,2,1,0,0,0};results[1]={2,2,1,0,0,0};metrics={};
 commit_hbm_kernel(negotiated.data(),negotiated.data(),negotiated.data(),negotiated.data(),tasks.data(),paths.data(),reads.data(),results.data(),3,2,4,1,&metrics);
 assert(results[0].status==4&&results[1].status==4&&metrics.commits==2&&metrics.conflicts==0);
 assert(negotiated[1].occupancy==2&&negotiated[2].occupancy==2);
 assert(negotiated[1].owner==0xffffffffU&&negotiated[2].owner==0xffffffffU);
 std::vector<Resource> replica0(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU}),replica1=replica0,replica2=replica0,replica3=replica0;
 tasks[0]={7,40,0,2,0,8,0,0,0};results[0]={0,2,1,0,0,0};metrics={};
 commit_hbm_kernel(replica0.data(),replica1.data(),replica2.data(),replica3.data(),tasks.data(),paths.data(),reads.data(),results.data(),3,1,4,1,&metrics);
 assert(results[0].status==4&&replica0[1].occupancy==1&&replica0[2].occupancy==1);
 assert(replica0[1].version==replica1[1].version&&replica0[1].version==replica2[1].version&&replica0[1].version==replica3[1].version);
 assert(replica0[2].owner==replica1[2].owner&&replica0[2].owner==replica2[2].owner&&replica0[2].owner==replica3[2].owner);
 std::vector<Resource> stale(MAX_RESOURCES,Resource{0,1,0,0,0,0xffffffffU});stale[1].version=7;
 std::vector<ReadEntry> stale_read(MAX_TX_ENTRIES);stale_read[0]={1,6};
 std::vector<PathResult> stale_result(MAX_TASKS);stale_result[0]={0,1,1,0,1,0};
 commit_hbm_kernel(stale.data(),stale.data(),stale.data(),stale.data(),tasks.data(),paths.data(),stale_read.data(),stale_result.data(),3,1,4,1,&metrics);
 assert(stale_result[0].status==4&&stale[1].occupancy==1&&stale[1].owner==tasks[0].net_id);
 std::cout<<"commit_hbm_tb: PASS\n";
}
