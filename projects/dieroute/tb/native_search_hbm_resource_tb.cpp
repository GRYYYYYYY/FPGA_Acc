#include "net_commit_fixture.hpp"
#include "native_search_hbm_resource.hpp"
using namespace commit_test;
int main(){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);
 NativeSearchResourceObservation output{};
 auto read=[&](unsigned node,std::uint64_t revision){return native_search_read_resource<16>(f.policy.data(),f.resources.data(),f.control,12,3,16,64,node,1,revision,3,output);};
 auto verify=[&](){auto before=f.state();for(unsigned n=0;n<12;++n){auto actual=f.resource(n);auto status=read(n,f.control.w[1]);check(status==(actual?NativeResourceReadStatus::present:NativeResourceReadStatus::absent),"presence mismatch");check(output.node==n&&output.owner==f.owner(n)&&output.session==1&&output.epoch==3,"observation identity");check(output.occupancy==(actual?actual->w[1]:0)&&output.history==(actual?actual->w[2]:0)&&output.version==(actual?actual->w[3]:0),"authority mismatch");}check(before==f.state(),"reader mutated authority");};
 verify();f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();verify();
 f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();verify();
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();verify();check(read(7,f.control.w[1])==NativeResourceReadStatus::present&&output.occupancy==2&&output.history==1,"negotiated resource cost");
 auto retained=output;check(read(7,f.control.w[1]+1)==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"revision rejection");
 auto saved=f.policy[7];f.policy[7]|=std::uint64_t(1)<<41;check(read(7,f.control.w[1])==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"policy rejection");f.policy[7]=saved;
}
