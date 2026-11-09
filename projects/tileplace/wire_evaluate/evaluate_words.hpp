#pragma once
#include "../wire_legality/trial_words.hpp"
#include "../wire_checks/guard_words.hpp"
#include "../wire_pipeline/touched_words.hpp"
#include "../wire_costs/cost_pair_words.hpp"
#include "../array_costs/score_array.hpp"
namespace tileplace_wire_evaluate {
struct Result {std::uint64_t before[4],after[4];std::int64_t score;std::uint32_t accepted,stage,status,touched_count;};
// Host validates canonical, disjoint backed arrays and unique trial IDs.
// Stage 1 legality, 2 guards, 3 touched discovery, 4 costs, 5 score.
// A legal rejection has stage 1/2 and status zero. Accepted means negative score.
inline Result evaluate(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* sites,std::uint64_t sc,const std::uint64_t* regions,std::uint64_t rc,const std::uint64_t* moves,std::uint32_t mc,const std::uint64_t* guards,std::uint64_t gc,const std::uint64_t* nets,std::uint64_t nc,const std::uint32_t* members,std::uint64_t member_count,const std::uint64_t* connections,std::uint64_t cc,const std::uint64_t* lines,std::uint64_t lc,const std::uint64_t* entries,std::uint64_t ec,const std::uint64_t* routed,std::uint64_t routed_count,const std::int32_t* weights,std::uint32_t* touched,std::uint32_t capacity){
 Result out{};std::uint32_t status;
 if(!tileplace_wire_legality::trial(blocks,positions,bc,sites,sc,regions,rc,moves,mc,status)){out.stage=1;out.status=status;return out;}
 if(!tileplace_wire_checks::guards(blocks,positions,bc,moves,mc,guards,gc,status)){out.stage=2;out.status=status;return out;}
 auto count=tileplace_wire_pipeline::touched(nets,nc,members,member_count,moves,mc,touched,capacity,status);if(status){out.stage=3;out.status=status;return out;}
 auto costs=tileplace_wire_costs::cost_pair_words(nets,nc,touched,count,blocks,positions,bc,members,member_count,connections,cc,lines,lc,entries,ec,routed,routed_count,moves,mc);if(costs.status){out.stage=4;out.status=costs.status;return out;}
 auto score=tileplace_cost_array::score_array(costs.before,costs.after,weights);if(score.status){out.stage=5;out.status=score.status;return out;}
 for(unsigned i=0;i<4;++i){out.before[i]=costs.before[i];out.after[i]=costs.after[i];}out.score=score.score;out.accepted=score.score<0;out.touched_count=count;return out;
}
}
