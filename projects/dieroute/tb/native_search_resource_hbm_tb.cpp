#include "net_commit_fixture.hpp"
#include "native_search_hbm_resource.hpp"
using namespace commit_test;
extern "C" void dieroute_native_search_resource_hbm(const std::uint64_t* policy,const dieroute::SummaryWord* resources,const std::uint64_t* control_words,std::uint64_t* output_words,std::uint32_t* status,std::uint32_t nodes,std::uint32_t dies,std::uint32_t shard_capacity,std::uint32_t tree_capacity,std::uint32_t node,std::uint64_t session,std::uint64_t revision,std::uint64_t epoch);
int main(){Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);
 NativeSearchResourceObservation output{};
 auto read=[&](unsigned node,std::uint64_t revision){alignas(64) std::uint64_t words[8];std::memcpy(words,&output,sizeof(output));std::uint32_t status=99;dieroute_native_search_resource_hbm(f.policy.data(),f.resources.data(),f.control.w,words,&status,12,3,16,64,node,1,revision,3);std::memcpy(&output,words,sizeof(output));return NativeResourceReadStatus(status);};
 auto verify=[&](){auto before=f.state();for(unsigned n=0;n<12;++n){auto actual=f.resource(n);auto status=read(n,f.control.w[1]);check(status==(actual?NativeResourceReadStatus::present:NativeResourceReadStatus::absent),"presence mismatch");check(output.node==n&&output.owner==f.owner(n)&&output.session==1&&output.epoch==3,"observation identity");check(output.occupancy==(actual?actual->w[1]:0)&&output.history==(actual?actual->w[2]:0)&&output.version==(actual?actual->w[3]:0),"authority mismatch");}check(before==f.state(),"reader mutated authority");};
 verify();f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9});f.branch(0,{1,3,5,7,9},0);f.run();verify();
 f.request(commit_proposal,1,20);f.footprint({6,7});f.branch(4,{6,7},1);f.run();verify();
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();verify();check(read(7,f.control.w[1])==NativeResourceReadStatus::present&&output.occupancy==2&&output.history==1,"negotiated resource cost");
 auto retained=output;check(read(7,f.control.w[1]+1)==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"revision rejection");
 auto saved=f.policy[7];f.policy[7]|=std::uint64_t(1)<<41;check(read(7,f.control.w[1])==NativeResourceReadStatus::invalid&&std::memcmp(&output,&retained,sizeof(output))==0,"policy rejection");f.policy[7]=saved;
}
