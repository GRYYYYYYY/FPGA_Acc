// XRT-only guard test: these exceptions must occur before a device launch.
#include "net_commit_fixture.hpp"
using namespace commit_test;
int main(){try{
 Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);
 auto* resource=const_cast<SummaryWord*>(f.resource(0));check(resource,"root not exported");
 std::array<SummaryWord*,4> authority={{resource,&f.trees[0],&f.nets[0],&f.control}};
 unsigned rejected=0;
 for(auto* p:authority){
  const auto original=*p;f.request(commit_query,0,10);f.command[0].w[7]=0;p->w[1]^=1;
  bool blocked=false;
  try{f.run();}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device net authority";}
  *p=original;check(blocked,"XRT accepted a host authority overwrite");++rejected;
  f.run();check(f.deltas[0].w[2]==1&&f.deltas[0].w[4]==1&&f.deltas[0].w[7]==1,"guard changed device authority");
 }
 check(f.calls==6&&rejected==4,"guard launch accounting");
 std::cout<<"XRT authority guard passed: rejected_host_overwrites="<<rejected<<" actual_kernel_calls="<<f.calls<<'\n';
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
