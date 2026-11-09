#ifdef NDEBUG
#undef NDEBUG
#endif
#include "direct_transaction.hpp"
#include <array>
#include <cassert>
int main(){
 uint64_t parents[]={UINT64_MAX,0,1,0},edges[]={0,41,42,99},targets[]={2,3};
 uint8_t reached_state[]={true,true,true,true};
 auto parent=[&](uint64_t n){return parents[n];};auto edge=[&](uint64_t n){return edges[n];};auto reached=[&](uint64_t n){return reached_state[n];};
 uint64_t scratch[4],staged[8],offsets[3];std::array<uint64_t,8> accepted;accepted.fill(77);std::array<uint64_t,3> accepted_offsets{{9,9,9}};uint64_t count=7,nt=2;
 routecast::SearchLabel labels[4];
 auto termination=routecast::SearchTermination::frontier_empty;
 auto run=[&](uint64_t sc,uint64_t ac){for(unsigned i=0;i<4;++i)labels[i]={0,0,parents[i],edges[i]};return routecast::direct_commit_paths(termination,0,4,targets,2,labels,reached_state,scratch,4,staged,sc,offsets,3,accepted.data(),ac,accepted_offsets.data(),3,count,nt);};
 auto prior=accepted;auto prior_offsets=accepted_offsets;
 for(auto status:{routecast::SearchTermination::work_budget,routecast::SearchTermination::frontier_capacity,routecast::SearchTermination::path_capacity,routecast::SearchTermination::unsupported_context,routecast::SearchTermination::invalid_input}){
 termination=status;auto got=run(8,8);auto expected=status==routecast::SearchTermination::work_budget?routecast::QueryStatus::work_budget:status==routecast::SearchTermination::frontier_capacity?routecast::QueryStatus::frontier_capacity:status==routecast::SearchTermination::path_capacity?routecast::QueryStatus::path_capacity:status==routecast::SearchTermination::unsupported_context?routecast::QueryStatus::unsupported_context:routecast::QueryStatus::invalid_input;assert(got==expected);assert(accepted==prior&&accepted_offsets==prior_offsets&&count==7&&nt==2);}
 termination=routecast::SearchTermination::targets_complete;reached_state[3]=false;assert(run(8,8)==routecast::QueryStatus::invalid_input);assert(accepted==prior&&count==7);
 termination=routecast::SearchTermination::frontier_empty;
 reached_state[3]=false;assert(run(8,8)==routecast::QueryStatus::unreachable);assert(accepted==prior&&accepted_offsets==prior_offsets&&count==7&&nt==2);reached_state[3]=true;
 assert(run(2,8)==routecast::QueryStatus::path_capacity);assert(accepted==prior&&count==7);
 assert(run(8,2)==routecast::QueryStatus::path_capacity);assert(accepted==prior&&accepted_offsets==prior_offsets&&count==7);
 parents[3]=99;assert(run(8,8)==routecast::QueryStatus::invalid_input);assert(accepted==prior&&count==7);parents[3]=0;
 assert(run(8,8)==routecast::QueryStatus::complete);assert(count==3&&nt==2);assert(accepted[0]==41&&accepted[1]==42&&accepted[2]==99);assert(accepted_offsets[0]==0&&accepted_offsets[1]==2&&accepted_offsets[2]==3);
}
