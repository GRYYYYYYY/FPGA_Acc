#pragma once
#include "enumerate_color_words.hpp"
#include "evaluate_batch_words.hpp"
#include "encode_rank_words.hpp"
#include "color_stats_words.hpp"
#include "external_forbidden_words.hpp"
#include "../wire_control/eligible_words.hpp"
namespace tileplace_wire_control_commit {
// CPU orchestration of integer data planes. This pointer-bearing wrapper is
// not an HLS top: synthesis must expose individual arrays as explicit ports.
struct ColorInput {
 const std::uint64_t *blocks,*units,*sites,*regions,*guards,*nets,*connections,*lines,*entries,*routed;
 std::uint64_t* positions;
 const std::uint32_t *unit_members,*net_members,*focus,*forbidden_indices;
 const std::int32_t* weights;
 std::uint64_t block_count,site_count,region_count,guard_count,net_count,connection_count,line_count,entry_count,routed_count,unit_member_count,net_member_count,focus_count;
 unsigned unit_count,forbidden_count,color,limit,chain_limit;
 int width,height;
 const ExternalForbidden* external_forbidden=nullptr;
};
struct ColorScratch {
 std::uint64_t *roots,*chain_roots,*first,*second,*merged,*descriptors,*source_trials,*groups,*scored,*conflicts,*writes,*candidates,*records,*identity_units,*identity_trials,*forbidden,*best7,*compact13;
 std::uint32_t *eligible,*owners,*touched,*diagnostics,*order,*selected,*group_indices,*gathered,*unique_indices;
 std::uint8_t* kinds;
 unsigned root_capacity,chain_capacity,move_capacity,record_capacity,owner_capacity,trial_capacity,group_capacity,write_capacity,touched_capacity,kind_capacity,identity_unit_capacity;
};
struct FullColorResult {unsigned stage,status,enumerated;std::uint64_t moved;ColorStats stats;};
// Validated canonical backing and pairwise disjoint scratch are prerequisites.
// Indexed forbidden candidates refer to this invocation's enumerated descriptors.
// Stage 1 eligibility, 2 enumeration, 3 batch evaluation, 4..8 encode/rank/commit.
inline FullColorResult full_color(const ColorInput& in,const ColorScratch& s){
 FullColorResult out{};unsigned status;
 auto eligible_count=tileplace_wire_control::eligible(in.units,in.unit_count,in.unit_members,in.unit_member_count,in.focus,in.focus_count,in.blocks,in.positions,in.block_count,in.width,in.height,in.color,s.eligible,s.group_capacity,status);
 if(status){out.stage=1;out.status=status;return out;}
 unsigned owner_used=0,trial_used=0;bool overflow=false;
 enumerate_color(s.eligible,eligible_count,in.units,in.unit_count,in.unit_members,in.blocks,in.positions,in.block_count,in.sites,in.site_count,in.width,in.height,in.limit,in.chain_limit,s.roots,s.root_capacity,s.chain_roots,s.chain_capacity,s.first,s.second,s.merged,s.move_capacity,s.descriptors,s.record_capacity,s.owners,s.owner_capacity,s.source_trials,s.trial_capacity,out.enumerated,owner_used,trial_used,overflow,status,s.groups,s.group_capacity);
 if(status){out.stage=2;out.status=status;return out;}
 auto evaluated=evaluate_batch(in.blocks,in.positions,in.block_count,in.sites,in.site_count,in.regions,in.region_count,in.guards,in.guard_count,in.nets,in.net_count,in.net_members,in.net_member_count,in.connections,in.connection_count,in.lines,in.line_count,in.entries,in.entry_count,in.routed,in.routed_count,in.weights,s.descriptors,out.enumerated,s.source_trials,trial_used,owner_used,s.scored,s.conflicts,s.record_capacity,s.writes,s.write_capacity,s.touched,s.touched_capacity,s.diagnostics);
 if(evaluated.status){out.stage=3;out.status=evaluated.status;return out;}
 if(in.external_forbidden){
  auto status=filter_external(s.scored,out.enumerated,s.owners,owner_used,in.units,in.unit_count,in.unit_members,in.unit_member_count,s.source_trials,trial_used,*in.external_forbidden,s.candidates,s.record_capacity,s.kinds,s.kind_capacity,s.identity_units,s.identity_unit_capacity,s.identity_trials,s.trial_capacity);
  if(status){out.stage=9;out.status=status;return out;}
 }
 auto result=encode_rank(s.scored,out.enumerated,s.owners,owner_used,in.units,in.unit_count,in.unit_members,in.unit_member_count,s.source_trials,trial_used,s.conflicts,s.writes,evaluated.writes,s.touched,evaluated.touched,s.owners,owner_used,in.blocks,in.block_count,in.positions,s.candidates,s.records,s.record_capacity,s.kinds,s.kind_capacity,s.identity_units,s.identity_unit_capacity,s.identity_trials,s.trial_capacity,s.order,s.selected,s.group_capacity,s.groups,eligible_count,in.forbidden_indices,in.forbidden_count,s.forbidden,s.best7,s.compact13,s.group_indices,s.gathered,s.unique_indices);
 if(result.status){out.stage=result.stage+3;out.status=result.status;return out;}
 out.moved=result.moved;out.stats=color_stats(eligible_count,s.scored,out.enumerated,s.selected,result);
 return out;
}
}
