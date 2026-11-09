#pragma once
#include "summary_hbm.hpp"
namespace dieroute {
constexpr std::uint64_t commit_none=UINT64_MAX;
enum NetCommitOp : std::uint64_t {commit_initialize=1,commit_start=2,commit_proposal=3,commit_ripup=4,commit_negotiate=5,commit_validate=6,commit_query=7};
enum NetCommitStatus : std::uint64_t {commit_ok=0,commit_bad_argument=1,commit_bad_session=2,commit_bad_record=3,commit_conflict=4,commit_bad_path=5,commit_no_space=6,commit_overflow=7,commit_bad_epoch=8};
// Commands are two 64-byte words. First: session,opcode,current revision,
// net slot,net ID,observed tree generation,present,root/node/history increment.
// Second: read count,shadow count,branch count,path count,next present,
// proposal overflow flag,0,0. Reads: {node:u64,version:u64}; paths:
// {node:u32,pip_key:u32,zero:u64}. Branch: attachment,sink,path offset,count,
// absolute depth,cost,0,0. Shadows: node,worker,occupancy,history,version,0,0,0.
// Policy: exclusive-net:u32, full die mask:u8 at bit32, forbidden:bit40.
// CSR arcs: destination:u32,pip_key:u32. All graph arrays are immutable.
// Resource: session,occupancy,history,version,node|mask<<32,member head,0,0.
// Tree/member: session,node,net slot,parent,pip,depth,next-net,next-resource.
// Net: session,net ID,root,tree head,count,generation,0,0.
// Control: session,revision,present,tree high-water,free head,
// node_count|dies<<32,shard_capacity|net_capacity<<32,tree_capacity.
// Each owner has a separate logical hash-table segment. This component uses
// one authority AXI master; physical owner-bank placement is a separate gate.
// Scratch uses pairs: {space,index,0,0,0,0,0,0}, replacement word. Scratch is
// speculative, never authoritative. Rejection preserves resources/trees/nets/
// control byte-for-byte. Successful calls publish only after all checks.
// Deltas: session,node|owner<<32,occupancy,history,version,new revision,mask,
// current-net membership (query only). Completion: status,revision,read checks,
// version conflicts,stale shadows,tree changed,staged words,delta count.
// Exclusive buffer handoff is required; no crash-atomic/concurrent-DMA claim.
extern "C" void dieroute_net_commit_hbm(
 const SummaryWord* command,const std::uint64_t* policy,const std::uint64_t* offsets,const std::uint64_t* arcs,
 const std::uint64_t* reads,const SummaryWord* shadows,const SummaryWord* branches,const std::uint64_t* paths,
 SummaryWord* resources,SummaryWord* trees,SummaryWord* nets,SummaryWord* control,SummaryWord* scratch,
 SummaryWord* deltas,SummaryWord* completion,
 std::uint32_t node_count,std::uint64_t arc_count,std::uint32_t dies,std::uint32_t shard_capacity,
 std::uint32_t net_capacity,std::uint32_t tree_capacity,std::uint32_t read_capacity,std::uint32_t shadow_capacity,
 std::uint32_t branch_capacity,std::uint32_t path_capacity,std::uint32_t scratch_capacity,std::uint32_t delta_capacity);
}
