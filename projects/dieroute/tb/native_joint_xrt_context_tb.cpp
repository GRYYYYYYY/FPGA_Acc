// XRT-only regression for cross-adapter image reuse and authority protection.
#include "net_commit_fixture.hpp"
#include "../host/xrt_device_context.hpp"
using namespace commit_test;
int main(){try{
 Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);
 auto& first=dieroute::xrt_host::device_context("DIEROUTE_NET_COMMIT_XCLBIN");
 auto& second=dieroute::xrt_host::device_context("DIEROUTE_OWNER_PUBLISH_XCLBIN");
 check(&first==&second,"adapters do not share the device context");
 bool blocked=false;
 try{dieroute::xrt_host::device_context("DIEROUTE_REJECTED_XCLBIN");}
 catch(const std::runtime_error& e){blocked=std::string(e.what())=="XRT adapters must share the same image file; refusing device reload";}
 check(blocked,"accepted a different image after authority initialization");
 auto query=[&](){f.request(commit_query,0,10);f.command[0].w[7]=0;f.run();check(f.deltas[0].w[2]==1&&f.deltas[0].w[4]==1&&f.deltas[0].w[7]==1,"device authority lost after context/overwrite guard");};
 query();
 auto* resource=const_cast<SummaryWord*>(f.resource(0));check(resource,"root not exported");
 std::array<SummaryWord*,4> authority={{resource,&f.trees[0],&f.nets[0],&f.control}};
 unsigned rejected=0;
 for(auto* p:authority){
  const auto original=*p;f.request(commit_query,0,10);f.command[0].w[7]=0;p->w[1]^=1;blocked=false;
  try{f.run();}catch(const std::runtime_error& e){blocked=std::string(e.what())=="host attempted to overwrite device net authority";}
  *p=original;check(blocked,"accepted CPU authority overwrite");++rejected;query();
 }
 check(f.calls==7&&rejected==4,"guard call accounting");
 std::cout<<"Joint XRT context guard passed: rejected_image_reload=1 rejected_host_overwrites="<<rejected<<" actual_kernel_calls="<<f.calls<<'\n';
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
