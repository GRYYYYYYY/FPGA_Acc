#include "net_commit_fixture.hpp"
using namespace commit_test;
#ifdef DIEROUTE_COMMIT_COMBINED_TB
int net_commit_adversarial_cases();
#endif
int main(){try{
 Fixture f;f.request(commit_initialize);f.run();f.start(0,10,0);f.start(1,20,4);f.start(2,30,8);
 f.request(commit_query,0,10);f.command[0].w[7]=11;f.run();check(f.deltas[0].w[2]==0&&!f.deltas[0].w[7],"absent interior query");
 f.request(commit_proposal,0,10);f.footprint({1,3,5,7,9,11});f.branch(0,{1,3,5,7,9},0);f.run();check(f.completion.w[7]==5,"cross-owner path publication");
 // A late invalid PIP must roll back earlier staged insertions.
 f.request(commit_proposal,2,30);f.footprint({7,10});f.branch(8,{10,7},2);f.paths[2]^=UINT64_C(1)<<32;f.run(commit_bad_path);
 f.request(commit_proposal,2,30);f.footprint({7,10});f.branch(8,{10,7},2);f.delta_capacity=1;f.run(commit_no_space);f.delta_capacity=32;
 f.scratch_capacity=2;f.run(commit_no_space);f.scratch_capacity=128;
 f.run();check(f.members(7)==std::set<unsigned>({10,30}),"exact shared-net membership");
 f.request(commit_proposal,1,20);f.footprint({3,6,7,11});f.branch(4,{6,7},1);f.reads[7]=1;f.run(commit_conflict);check(f.completion.w[2]==4&&f.completion.w[3]==1,"off-path absent read omitted");
 f.reads[7]=0;f.run();check(f.members(7).size()==3,"three-way congestion membership");
 f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;f.run();check(f.resource(7)->w[2]==2&&f.control.w[2]==2,"negotiated history/epoch");
 f.request(commit_validate,0,10);f.footprint({3,7,11});f.command[1].w[1]=1;f.shadows[0].w[0]=7;f.shadows[0].w[1]=2;f.shadows[0].w[2]=3;f.shadows[0].w[3]=1;f.shadows[0].w[4]=f.version(7);f.run(commit_conflict);check(f.completion.w[4]==1,"stale consumed history ignored");
 f.shadows[0].w[3]=2;f.run();
 f.command[0].w[5]--;f.run(commit_conflict);check(f.completion.w[5]==1,"stale net generation ignored");
 f.request(commit_query,0,10);f.command[0].w[7]=7;f.run();check(f.deltas[0].w[7]==1&&f.deltas[0].w[2]==3,"net membership query");
 f.request(commit_ripup,0,10);f.run();check(f.members(7)==std::set<unsigned>({20,30})&&f.resource(1)->w[1]==0&&f.resource(1)->w[3]==2,"ripup sharing/tombstones");
 auto high=f.control.w[3];f.request(commit_proposal,0,10);f.footprint({1,3,5});f.branch(0,{1,3,5},0);f.run();check(f.control.w[3]==high,"released entries not reused");
 f.request(commit_proposal,0,10);f.footprint({1,3});f.branch(3,{1},0);f.run(commit_bad_path);
 f.request(commit_proposal,0,10);f.footprint({2,11});f.branch(0,{2,11},0);f.branches[0].w[5]++;f.run(commit_bad_path);
 f.branches[0].w[5]--;f.command[0].w[6]--;f.run(commit_bad_epoch);
 f.command[0].w[6]++;f.command[0].w[2]--;f.run(commit_bad_epoch);
 f.command[0].w[2]++;f.command[0].w[0]--;f.run(commit_bad_session);
 f.command[0].w[0]++;f.policy[11]|=UINT64_C(1)<<40;f.run(commit_bad_path);f.policy[11]&=~(UINT64_C(1)<<40);
 f.policy[11]=(f.policy[11]&~UINT64_C(0xffffffff))|20;f.run(commit_bad_path);f.policy[11]|=UINT32_MAX;
 f.command[1].w[5]=1;f.run(commit_overflow);f.command[1].w[5]=0;
 f.reads[2]=2;f.run(commit_bad_argument);f.reads[2]=11;
 f.run();
 f.request(commit_ripup,1,20);f.run();f.request(commit_ripup,2,30);f.run();
 f.request(commit_negotiate);f.command[0].w[7]=0;f.command[1].w[4]=4;f.run();
 f.request(commit_validate,0,10);f.footprint({0,1,2,3,5,7,9,11});f.run();
 // New session invalidates all old trees and owner tags without host clearing.
 ++f.session;f.request(commit_initialize);f.command[0].w[6]=1;f.run();f.start(0,10,0);
 f.request(commit_initialize);f.command[0].w[5]=0;f.run(commit_bad_session);
 std::cout<<"whole-net commit: all-owner read validation, exact membership/tree state, atomic rejection, shared congestion, ripup/reuse and session reset passed; launches="<<f.calls<<'\n';
#ifdef DIEROUTE_COMMIT_COMBINED_TB
 check(net_commit_adversarial_cases()==0,"adversarial suite failed");
#endif
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
