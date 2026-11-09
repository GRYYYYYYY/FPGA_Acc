#pragma once
#include "full_color_words.hpp"
#include "../cpp_snapshot/transactions.hpp"
namespace tileplace_wire_control_commit {
struct HostProposals {std::vector<tileplace_snapshot::Proposal> proposals;ColorStats stats;};
// Run the complete integer pipeline on private positions, then decode selected
// records for the existing native proposal protocol. Actual commit remains an
// explicit caller operation; input placement is unchanged on success or error.
inline HostProposals propose(ColorInput input,const ColorScratch& scratch){
 if(input.block_count>SIZE_MAX/2)throw std::length_error("proposal positions too large");
 std::vector<std::uint64_t> private_positions(input.positions,input.positions+2*input.block_count);
 input.positions=private_positions.data();
 auto result=full_color(input,scratch);
 if(result.stage||result.status||result.stats.status)throw std::invalid_argument("full color proposal stage "+std::to_string(result.stage)+" status "+std::to_string(result.status));
 HostProposals output;output.stats=result.stats;
 const std::string names[5]={"move","swap","macro_swap","chain2","chain3"};
 auto point=[](const std::uint64_t* p){return tileplace_snapshot::Point{int(tileplace_wire_best::signed32(p[0])),int(tileplace_wire_best::signed32(p[0]>>32)),int(tileplace_wire_best::signed32(p[1])),int(tileplace_wire_best::signed32(p[1]>>32))};};
 for(unsigned i=0;i<result.stats.accepted;++i){auto index=scratch.selected[i];auto d=scratch.scored+6ULL*index;auto c=scratch.conflicts+6ULL*index;tileplace_snapshot::Proposal proposal;
  proposal.kind=names[d[1]];proposal.score=tileplace_wire_best::score(d[0]);
  for(std::uint64_t j=0;j<d[3];++j){auto owner=scratch.owners[d[2]+j];auto u=input.units+4ULL*owner;proposal.units.emplace_back(input.unit_members+u[0],input.unit_members+u[0]+u[1]);}
  std::sort(proposal.units.begin(),proposal.units.end());
  for(std::uint64_t j=0;j<d[5];++j){auto t=scratch.source_trials+3*(d[4]+j);proposal.trial[std::uint32_t(t[0])]=point(t+1);}
  for(std::uint64_t j=0;j<c[1];++j)proposal.write_sites.insert(point(scratch.writes+2*(c[0]+j)));
  for(std::uint64_t j=0;j<c[3];++j)proposal.touched_nets.insert(scratch.touched[c[2]+j]);
  output.proposals.push_back(std::move(proposal));
 }
 return output;
}
}
