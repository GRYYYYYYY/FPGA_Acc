#pragma once
#include "control_commit_words.hpp"
namespace tileplace_wire_control_commit {
struct ColorStats {unsigned eligible,proposals,accepted,rejected,kinds[5],status;};
// Only consume a successful encode_rank result and its original descriptor
// indices. Fixed units still contribute to eligible; proposals is the count
// AFTER per-group best and identity dedup, before conflict selection.
inline ColorStats color_stats(unsigned eligible,const std::uint64_t* descriptors,
 unsigned count,const std::uint32_t* selected,const Result& result){
 ColorStats stats{};
 if(result.stage||result.status||result.selected>result.proposals){stats.status=1;return stats;}
 for(unsigned i=0;i<result.selected;++i)if(selected[i]>=count||descriptors[6ULL*selected[i]+1]>4){stats.status=2;return stats;}
 stats.eligible=eligible;stats.proposals=result.proposals;stats.accepted=result.selected;stats.rejected=result.proposals-result.selected;
 for(unsigned i=0;i<result.selected;++i)++stats.kinds[descriptors[6ULL*selected[i]+1]];
 return stats;
}
}
