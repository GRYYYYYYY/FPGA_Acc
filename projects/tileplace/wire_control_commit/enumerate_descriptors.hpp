#pragma once
#include "../wire_candidates/root_words.hpp"
#include "../wire_candidates/translation_words.hpp"
#include "../wire_enumeration/owners_words.hpp"
#include "../wire_trial_build/chain_words.hpp"
#include "../wire_enumerator/merge_core.hpp"
namespace tileplace_wire_descriptor_enumerator {

// Variable-length candidate pools; never truncate macro trials to a fixed record.
// Capacity counts descriptors, owner IDs and trial records, not words.
inline void collect(std::uint64_t* descriptors,unsigned capacity,std::uint32_t* owners,unsigned owner_capacity,std::uint64_t* trials,unsigned trial_capacity,unsigned& emitted,unsigned& owner_used,unsigned& trial_used,bool& overflow,unsigned kind,const unsigned* moved,unsigned owner_count,const std::uint64_t* trial,unsigned trial_count){
 if(emitted>=capacity||owner_used>owner_capacity||owner_count>owner_capacity-owner_used||trial_used>trial_capacity||trial_count>trial_capacity-trial_used){overflow=true;return;}
 auto d=descriptors+6ULL*emitted;d[0]=0;d[1]=kind;d[2]=owner_used;d[3]=owner_count;d[4]=trial_used;d[5]=trial_count;
 for(unsigned i=0;i<owner_count;++i)owners[owner_used+i]=moved[i];
 for(unsigned i=0;i<trial_count;++i){trials[3ULL*(trial_used+i)]=trial[3ULL*i];trials[3ULL*(trial_used+i)+1]=trial[3ULL*i+1];trials[3ULL*(trial_used+i)+2]=trial[3ULL*i+2];}
 ++emitted;owner_used+=owner_count;trial_used+=trial_count;
}

// Kind IDs: move=0, swap=1, macro_swap=2, chain2=3, chain3=4.
// Host validates canonical Unit4 records, member ranges/IDs, disjoint backed scratch.
// Emit(kind, unit-index array, unit count, trial words, trial count) consumes each trial synchronously.
// No candidate filtering/scoring here: every branch-generated trial is emitted in native order.
// Errors may follow earlier emissions; caller must discard the whole batch on status != 0.
inline tileplace_hbm::Location root(const std::uint64_t* units,const std::uint32_t* members,unsigned unit,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc){auto id=members[units[4ULL*unit]];auto i=tileplace_wire_candidates::block_index(blocks,bc,id);return tileplace_wire_candidates::location(positions+2*i);}
inline void enumerate(unsigned owner,const std::uint64_t* units,std::uint32_t uc,const std::uint32_t* members,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint64_t* sites,std::uint64_t sc,int width,int height,unsigned limit,unsigned chain_limit,std::uint64_t* roots,unsigned root_capacity,std::uint64_t* chain_roots,unsigned chain_capacity,std::uint64_t* first,std::uint64_t* second,std::uint64_t* merged,unsigned move_capacity,std::uint64_t* descriptors,unsigned descriptor_capacity,std::uint32_t* output_owners,unsigned owner_capacity,std::uint64_t* output_trials,unsigned trial_capacity,unsigned& emitted,unsigned& owner_used,unsigned& trial_used,bool& overflow,unsigned& status){
 status=0;if(owner>=uc){status=1;return;}auto unit=units+4ULL*owner;auto size=unit[1];if(!size||size>UINT32_MAX||bc>UINT64_MAX/8||sc>UINT64_MAX/4){status=1;return;}if(std::uint32_t(unit[2]))return;
 auto own=members+unit[0];auto source=root(units,members,owner,blocks,positions,bc);std::uint64_t source_words[2];tileplace_wire_candidates::store(source_words,source);
 auto index=tileplace_wire_candidates::block_index(blocks,bc,own[0]);auto type=std::uint32_t(blocks[8*index]>>32);
 auto nr=tileplace_wire_candidates::roots(sites,sc,source_words,type,width,height,limit,roots,root_capacity,status);if(status)return;
 for(unsigned r=0;r<nr;++r){auto target=roots+2ULL*r;auto n=tileplace_wire_candidates::translate(blocks,positions,bc,own,size,target,first,move_capacity,status);if(status)return;
 auto owners=tileplace_wire_enumeration::owners(blocks,positions,bc,own,size,first,n);if(owners.status){status=owners.status;return;}unsigned moved[3]={owner,0,0};
 if(!owners.count){collect(descriptors,descriptor_capacity,output_owners,owner_capacity,output_trials,trial_capacity,emitted,owner_used,trial_used,overflow,0,moved,1,first,n);if(overflow){status=5;return;}continue;}if(owners.count!=1)continue;auto other=owners.unit;if(other>=uc){status=1;return;}auto v=units+4ULL*other;if(other==owner||std::uint32_t(v[2]))continue;auto vm=members+v[0];auto other_source=root(units,members,other,blocks,positions,bc);std::uint64_t other_words[2];tileplace_wire_candidates::store(other_words,other_source);moved[1]=other;
 if(size==v[1]&&tileplace_wire_checks::shape(blocks,positions,bc,own,size,vm,v[1],status)){
 auto a=tileplace_wire_candidates::translate(blocks,positions,bc,own,size,other_words,first,move_capacity,status);if(status)return;auto b=tileplace_wire_candidates::translate(blocks,positions,bc,vm,v[1],source_words,second,move_capacity,status);if(status)return;auto count=tileplace_wire_enumerator_merge::merge(first,a,second,b,merged,move_capacity,status);if(status)return;collect(descriptors,descriptor_capacity,output_owners,owner_capacity,output_trials,trial_capacity,emitted,owner_used,trial_used,overflow,size==1?1:2,moved,2,merged,count);if(overflow){status=5;return;}
 }if(status)return;if(size!=1||v[1]!=1)continue;
 auto vi=tileplace_wire_candidates::block_index(blocks,bc,vm[0]);auto vt=std::uint32_t(blocks[8*vi]>>32);auto cr=tileplace_wire_candidates::roots(sites,sc,other_words,vt,width,height,chain_limit,chain_roots,chain_capacity,status);if(status)return;
 for(unsigned c=0;c<cr;++c){auto next=chain_roots+2ULL*c;if(tileplace_wire_checks::equal(tileplace_wire_candidates::location(next),other_source))continue;auto occupant=tileplace_wire_checks::occupant(blocks,positions,bc,next,status);if(status)return;unsigned ids[3]={own[0],vm[0],0};
 if(!occupant.found){auto count=tileplace_wire_trial_build::chain(blocks,positions,bc,ids,2,target,next,merged,move_capacity,status);if(status)return;collect(descriptors,descriptor_capacity,output_owners,owner_capacity,output_trials,trial_capacity,emitted,owner_used,trial_used,overflow,3,moved,2,merged,count);if(overflow){status=5;return;}continue;}
 auto third=occupant.unit_id;if(third>=uc){status=1;return;}auto w=units+4ULL*third;if(w[1]!=1||third==owner||third==other||std::uint32_t(w[2]))continue;moved[2]=third;ids[2]=members[w[0]];auto count=tileplace_wire_trial_build::chain(blocks,positions,bc,ids,3,target,next,merged,move_capacity,status);if(status)return;collect(descriptors,descriptor_capacity,output_owners,owner_capacity,output_trials,trial_capacity,emitted,owner_used,trial_used,overflow,4,moved,3,merged,count);if(overflow){status=5;return;}
 }
 }
}
}
