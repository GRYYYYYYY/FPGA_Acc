#pragma once
#include "identity_words.hpp"
namespace tileplace_wire_best {
inline bool valid_identity(const std::uint64_t* a,std::uint64_t kc,std::uint64_t uc,std::uint64_t tc){return tileplace_hbm::valid_range(range(a),kc)&&tileplace_hbm::valid_range(range(a+2),uc)&&tileplace_hbm::valid_range(range(a+4),tc);}
inline std::int64_t score(std::uint64_t w){return w<=INT64_MAX?std::int64_t(w):-1-std::int64_t(UINT64_MAX-w);}
// Candidates are seven words: score then full six-word identity. Groups are offset/count pairs.
// Forbidden identities reference the same kind/unit/member/trial pools. Output UINT32_MAX means no best.
// Host validates pool backing and canonical identities. Validate before writing any output.
// Status 1 group range, 2 capacity, 3 identity/range/scaling.
inline std::uint32_t best(const std::uint64_t* candidates,std::uint32_t cc,const std::uint64_t* groups,std::uint32_t gc,const std::uint64_t* forbidden,std::uint32_t fc,const std::uint8_t* kinds,std::uint64_t kc,const std::uint64_t* units,std::uint64_t uc,const std::uint32_t* members,std::uint64_t mc,const std::uint64_t* trials,std::uint64_t tc,std::uint32_t* output,std::uint32_t capacity,std::uint32_t& status){
 status=0;if(gc>capacity){status=2;return 0;}if(uc>UINT64_MAX/2||tc>UINT64_MAX/3){status=3;return 0;}
 for(std::uint32_t i=0;i<gc;++i)if(!tileplace_hbm::valid_range(range(groups+2ULL*i),cc)){status=1;return 0;}
 for(std::uint64_t i=0;i<uc;++i)if(!tileplace_hbm::valid_range(range(units+2*i),mc)){status=3;return 0;}
 for(std::uint32_t i=0;i<cc;++i)if(!valid_identity(candidates+7ULL*i+1,kc,uc,tc)){status=3;return 0;}
 for(std::uint32_t i=0;i<fc;++i)if(!valid_identity(forbidden+6ULL*i,kc,uc,tc)){status=3;return 0;}
 std::uint32_t found=0;
 for(std::uint32_t g=0;g<gc;++g){auto group=range(groups+2ULL*g);std::uint32_t chosen=UINT32_MAX;
 for(std::uint64_t j=0;j<group.count;++j){auto index=std::uint32_t(group.offset+j);auto c=candidates+7ULL*index;if(score(c[0])>=0)continue;bool blocked=false;for(std::uint32_t f=0;f<fc;++f)blocked|=identity(c+1,forbidden+6ULL*f,kinds,units,members,trials)==0;if(blocked)continue;
 if(chosen==UINT32_MAX){chosen=index;continue;}auto old=candidates+7ULL*chosen;if(score(c[0])<score(old[0])||(score(c[0])==score(old[0])&&identity(c+1,old+1,kinds,units,members,trials)<0))chosen=index;
 }output[g]=chosen;found+=chosen!=UINT32_MAX;
 }return found;
}
}
