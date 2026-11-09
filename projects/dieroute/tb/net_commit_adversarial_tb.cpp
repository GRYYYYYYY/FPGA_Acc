#include "net_commit_fixture.hpp"
using namespace commit_test;
namespace {
unsigned calls=0;
void invoke(Fixture& f,std::uint64_t expected,unsigned shard=16,unsigned pool=64,
            unsigned read_cap=32,unsigned path_cap=32){
 auto before=f.state();
 dieroute_net_commit_hbm(f.command.data(),f.policy.data(),f.offsets.data(),f.arcs.data(),
  f.reads.data(),f.shadows.data(),f.branches.data(),f.paths.data(),f.resources.data(),
  f.trees.data(),f.nets.data(),&f.control,f.scratch.data(),f.deltas.data(),&f.completion,
  12,f.arc_count,3,shard,8,pool,read_cap,16,16,path_cap,f.scratch_capacity,f.delta_capacity);
 ++calls;
 check(f.completion.w[0]==expected,"adversarial call "+std::to_string(calls)+" status "+std::to_string(f.completion.w[0])+" expected "+std::to_string(expected));
 if(expected!=commit_ok)check(before==f.state(),"adversarial rejection partially published");
}
void init(Fixture& f,unsigned shard=16,unsigned pool=64){f.request(commit_initialize);invoke(f,commit_ok,shard,pool);}
void start(Fixture& f,unsigned slot,unsigned id,unsigned root,unsigned shard=16,unsigned pool=64,std::uint64_t result=commit_ok){f.request(commit_start,slot,id);f.command[0].w[7]=root;invoke(f,result,shard,pool);}
SummaryWord& record(Fixture& f,unsigned node){auto p=f.resource(node);check(p,"missing resource for injection");return *const_cast<SummaryWord*>(p);}
}
int net_commit_adversarial_cases(){try{
 // Net identity must be unique even when roots and slots differ.
 {Fixture f;init(f);start(f,0,10,0);start(f,1,10,4,16,64,commit_bad_argument);}
 // Exhaust one logical owner without consuming the other owners' capacity.
 {Fixture f;init(f,1);start(f,0,10,0,1);start(f,1,20,1,1,64,commit_no_space);
  f.request(commit_query,0,10);f.command[0].w[7]=1;invoke(f,commit_ok,1);check(!f.deltas[0].w[2]&&!f.deltas[0].w[4],"full hash absent read is not zero");
  start(f,1,20,4,1);start(f,2,30,8,1);
  f.request(commit_proposal,0,10);f.footprint({1,3});f.branch(0,{1,3},0);invoke(f,commit_no_space,1);
 }
 // Global tree pool exhaustion must undo a newly staged resource and net.
 {Fixture f;init(f,16,1);start(f,0,10,0,16,1);start(f,1,20,4,16,1,commit_no_space);}
 // Reject descriptor counts before dereferencing nonexistent payload entries.
 {Fixture f;init(f);start(f,0,10,0);
  f.request(commit_validate,0,10);f.command[1].w[0]=UINT64_MAX;invoke(f,commit_bad_argument);
  f.request(commit_proposal,0,10);f.command[1].w[3]=UINT64_MAX;invoke(f,commit_bad_argument);
  f.request(commit_validate,0,10);f.command[1].w[1]=17;invoke(f,commit_bad_argument);
  f.request(commit_proposal,0,10);f.command[1].w[2]=17;invoke(f,commit_bad_argument);
  f.request(commit_proposal,0,10);f.footprint({1,3});f.branch(0,{1,3},0);invoke(f,commit_bad_argument,16,64,1);
  invoke(f,commit_bad_argument,16,64,32,1);
  // A failure in branch two must discard the completely valid first branch.
  f.request(commit_proposal,0,10);f.footprint({1,2,3,11});f.branch(0,{1,3},0);f.branch(0,{2,11},0);f.branches[1].w[5]++;invoke(f,commit_bad_path);
  f.branches[1].w[5]--;invoke(f,commit_ok);f.verify();
  auto saved=record(f,11);record(f,11).w[3]=UINT64_MAX;
  f.request(commit_ripup,0,10);invoke(f,commit_overflow);record(f,11)=saved;
  // A generation overflow occurs only after staging the otherwise valid path.
  auto gen=f.nets[0].w[5];f.nets[0].w[5]=UINT64_MAX;
  f.request(commit_proposal,0,10);f.footprint({5});f.branch(3,{5},0);invoke(f,commit_overflow);f.nets[0].w[5]=gen;
  auto rev=f.control.w[1];f.control.w[1]=UINT64_MAX;
  f.request(commit_ripup,0,10);invoke(f,commit_overflow);
  f.request(commit_validate,0,10);f.footprint({1,2,3,11});auto before=f.state();invoke(f,commit_ok);check(before==f.state(),"validation at max revision changed state");
  f.control.w[1]=rev;
 }
 // Overflow boundary inputs are deliberately injected states, not reachable
 // claims about test duration. Every failure compares all authority bytes.
 {Fixture f;init(f);start(f,0,10,0);start(f,1,20,4);
  f.request(commit_proposal,0,10);f.footprint({1,3});f.branch(0,{1,3},0);invoke(f,commit_ok);
  auto original=record(f,3);record(f,3).w[2]=UINT64_MAX-1;
  f.request(commit_proposal,1,20);f.footprint({3});f.branch(4,{3},1);invoke(f,commit_overflow);
  record(f,3)=original;record(f,3).w[3]=UINT64_MAX;
  f.request(commit_proposal,1,20);f.footprint({3});f.branch(4,{3},1);invoke(f,commit_overflow);
  record(f,3)=original;
  f.request(commit_proposal,1,20);f.footprint({3});f.branch(4,{3},1);invoke(f,commit_ok);
  original=record(f,3);record(f,3).w[2]=UINT64_MAX-1;
  f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;invoke(f,commit_overflow);
  record(f,3)=original;record(f,3).w[3]=UINT64_MAX;
  f.request(commit_negotiate);f.command[0].w[7]=1;f.command[1].w[4]=2;invoke(f,commit_overflow);
  record(f,3)=original;
  auto present=f.control.w[2];f.control.w[2]=UINT64_MAX;
  f.request(commit_proposal,1,20);f.footprint({1});f.branch(3,{1},1);invoke(f,commit_overflow);f.control.w[2]=present;
  // A malformed membership chain must fail without changing any authority.
  original=record(f,3);record(f,3).w[5]=64;
  f.request(commit_query,0,10);f.command[0].w[7]=3;invoke(f,commit_bad_record);record(f,3)=original;
  auto e=f.trees[f.nets[0].w[3]];f.trees[f.nets[0].w[3]].w[6]=f.nets[0].w[3];
  f.request(commit_ripup,0,10);invoke(f,commit_bad_record);f.trees[f.nets[0].w[3]]=e;f.verify();
 }
 std::cout<<"net commit adversarial: owner/tree capacity, descriptor bounds, late multi-branch rollback, version/history/cost/generation/revision overflow and malformed chains passed; calls="<<calls<<'\n';
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
#ifndef DIEROUTE_COMMIT_COMBINED_TB
int main(){return net_commit_adversarial_cases();}
#endif
