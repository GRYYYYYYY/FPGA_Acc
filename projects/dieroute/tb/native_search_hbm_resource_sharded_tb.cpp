#include "net_commit_fixture.hpp"
#include "native_search_hbm_resource_sharded.hpp"
#include <iostream>
using namespace commit_test;
int main(){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);
 NativeSearchResourceObservation output{};
 unsigned calls=0;auto read=[&](unsigned node,std::uint64_t revision){
 auto expected_output=output;auto expected=native_search_read_resource<16>(f.policy.data(),f.resources.data(),f.control,12,3,16,64,node,1,revision,3,expected_output);
 std::array<std::array<SummaryWord,24>,3> banks{};SummaryWord sentinel{};for(auto& w:sentinel.w)w=UINT64_C(0xa5912f73d26be048);
 for(unsigned owner=0;owner<3;++owner){banks[owner].fill(sentinel);std::memcpy(banks[owner].data()+4,f.resources.data()+owner*16,16*64);}auto before=banks;
 auto actual=native_search_read_resource_sharded<16>(f.policy.data(),banks[0].data()+4,banks[1].data()+4,banks[2].data()+4,f.control,12,3,16,64,node,1,revision,3,output);
 check(actual==expected&&!std::memcmp(&output,&expected_output,64),"sharded observation/status differential");check(!std::memcmp(banks.data(),before.data(),sizeof(banks)),"reader changed physical bank/guard");++calls;return actual;};
 auto verify=[&](){auto before=f.state();for(unsigned n=0;n<12;++n){auto actual=f.resource(n);auto status=read(n,f.control.w[1]);check(status==(actual?NativeResourceReadStatus::present:NativeResourceReadStatus::absent),"presence mismatch");check(output.node==n&&output.owner==f.owner(n)&&output.session==1&&output.epoch==3,"observation identity");check(output.occupancy==(actual?actual->w[1]:0)&&output.history==(actual?actual->w[2]:0)&&output.version==(actual?actual->w[3]:0),"authority mismatch");}check(before==f.state(),"reader mutated authority");};
 verify();f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();verify();
 f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();verify();
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();verify();check(read(7,f.control.w[1])==NativeResourceReadStatus::present&&output.occupancy==2&&output.history==1,"negotiated resource cost");
 auto retained=output;check(read(7,f.control.w[1]+1)==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"revision rejection");
 auto saved=f.policy[7];f.policy[7]|=std::uint64_t(1)<<41;check(read(7,f.control.w[1])==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"policy rejection");f.policy[7]=saved;
 for(unsigned dies=1;dies<=3;++dies){
  std::array<std::uint64_t,3> policy{};for(unsigned n=0;n<3;++n)policy[n]=UINT32_MAX|(std::uint64_t(1u<<(n%dies))<<32);
  SummaryWord control{};control.w[0]=9;control.w[1]=3;control.w[5]=3|(std::uint64_t(dies)<<32);control.w[6]=4|(std::uint64_t(3)<<32);control.w[7]=64;
  std::array<SummaryWord,12> flat{};flat[0]={{9,1,2,5,std::uint64_t(1)<<32,7,0,0}};
  for(unsigned n=0;n<3;++n){NativeSearchResourceObservation a{},b{};auto expected=native_search_read_resource<4>(policy.data(),flat.data(),control,3,dies,4,64,n,9,3,1,a);auto actual=native_search_read_resource_sharded<4>(policy.data(),flat.data(),dies>1?flat.data()+4:nullptr,dies>2?flat.data()+8:nullptr,control,3,dies,4,64,n,9,3,1,b);check(actual==expected&&!std::memcmp(&a,&b,64),"inactive owner port dereference or low-die mismatch");++calls;}
 }
 auto preserved=output;auto unsupported=f.control;unsupported.w[5]=12|(std::uint64_t(4)<<32);
 check(native_search_read_resource_sharded<16>(nullptr,nullptr,nullptr,nullptr,unsupported,12,4,16,64,0,1,unsupported.w[1],3,output)==NativeResourceReadStatus::invalid&&!std::memcmp(&output,&preserved,64),"unsupported owner count must reject before any bank/policy access");
 std::cout<<"SHARDED_RESOURCE_DIFFERENTIAL calls="<<calls<<" snapshots=4\n";
}
