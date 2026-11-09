#pragma once
#include "../wire_evaluate/evaluate_words.hpp"
#include "../wire_pipeline/write_sites_words.hpp"
namespace tileplace_wire_control_commit {
// Keep descriptor indices stable: unchanged/rejected candidates receive zero score.
// Changed accepted candidates produce old/new write-site unions and touched-net ranges.
// Error scratch is discardable; input positions are never modified. Diagnostics4
// preserves evaluator stage/status, changed and accepted. Stage 1 input, 2 writes, 3 evaluator.
struct BatchResult {unsigned stage,status,index,accepted,writes,touched;};
inline BatchResult evaluate_batch(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* sites,std::uint64_t sc,const std::uint64_t* regions,std::uint64_t rc,const std::uint64_t* guards,std::uint64_t gc,const std::uint64_t* nets,std::uint64_t nc,const std::uint32_t* members,std::uint64_t member_count,const std::uint64_t* connections,std::uint64_t cc,const std::uint64_t* lines,std::uint64_t lc,const std::uint64_t* entries,std::uint64_t ec,const std::uint64_t* routed,std::uint64_t routed_count,const std::int32_t* weights,const std::uint64_t* descriptors,std::uint32_t count,const std::uint64_t* trials,std::uint64_t trial_count,std::uint64_t owner_count,std::uint64_t* scored,std::uint64_t* conflicts,std::uint32_t record_capacity,std::uint64_t* writes,std::uint32_t write_capacity,std::uint32_t* touched,std::uint32_t touched_capacity,std::uint32_t* diagnostics){
 BatchResult out{};
 if(count>record_capacity){out.stage=1;out.status=2;return out;}
 if(trial_count>UINT64_MAX/3){out.stage=1;out.status=3;return out;}
 for(std::uint32_t i=0;i<count;++i){auto d=descriptors+6ULL*i;
  if(d[1]>4||!d[3]||d[3]>3||!d[5]||d[5]>UINT32_MAX||!tileplace_hbm::valid_range({d[2],d[3]},owner_count)||!tileplace_hbm::valid_range({d[4],d[5]},trial_count)){out.stage=1;out.status=1;return out;}
  for(std::uint64_t j=0;j<d[5];++j)if(trials[3*(d[4]+j)]>UINT32_MAX){out.stage=1;out.status=1;return out;}
 }
 for(std::uint32_t i=0;i<count;++i){auto d=descriptors+6ULL*i;auto trial=trials+3*d[4];out.index=i;
  for(unsigned j=0;j<6;++j)scored[6ULL*i+j]=d[j];
  scored[6ULL*i]=0;
  auto w=tileplace_wire_pipeline::write_sites(blocks,positions,bc,trial,std::uint32_t(d[5]),writes+2ULL*out.writes,write_capacity-out.writes);
  if(w.status){out.stage=2;out.status=w.status;return out;}
  auto c=conflicts+6ULL*i;c[0]=out.writes;c[1]=w.count;c[2]=out.touched;c[3]=0;c[4]=d[2];c[5]=d[3];out.writes+=w.count;
  diagnostics[4ULL*i]=0;diagnostics[4ULL*i+1]=0;diagnostics[4ULL*i+2]=w.changed;diagnostics[4ULL*i+3]=0;
  if(!w.changed)continue;
  auto r=tileplace_wire_evaluate::evaluate(blocks,positions,bc,sites,sc,regions,rc,trial,std::uint32_t(d[5]),guards,gc,nets,nc,members,member_count,connections,cc,lines,lc,entries,ec,routed,routed_count,weights,touched+out.touched,touched_capacity-out.touched);
  diagnostics[4ULL*i]=r.stage;diagnostics[4ULL*i+1]=r.status;diagnostics[4ULL*i+3]=r.accepted;
  if(r.status){out.stage=3;out.status=r.status;return out;}
  if(!r.accepted)continue;
  scored[6ULL*i]=std::uint64_t(r.score);c[3]=r.touched_count;out.touched+=r.touched_count;++out.accepted;
 }
 out.index=count;return out;
}
}
