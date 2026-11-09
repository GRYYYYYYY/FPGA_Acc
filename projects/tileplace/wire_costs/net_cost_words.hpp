#pragma once
#include "../wire_pressure/pressure_words.hpp"
namespace tileplace_wire_costs {
using namespace tileplace_hbm;
struct Result {std::uint64_t costs[3];std::uint32_t status,reserved;};
// Snapshot ABI block records: 8 words; positions: 2; connections: 2.
// Trial record: ID word followed by 2 location words. Host validates canonical
// ordering, endpoint membership, unique trial IDs and backing capacities.
inline Location location(const std::uint64_t* w){return {tileplace_wire::signed_word(w[0]),tileplace_wire::signed_word(w[0]>>32),tileplace_wire::signed_word(w[1]),tileplace_wire::signed_word(w[1]>>32)};}
inline bool position(const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t count,const std::uint64_t* moves,std::uint32_t mc,std::uint32_t id,Location& p){
 std::uint64_t low=0,high=count;while(low<high){auto mid=low+(high-low)/2;if(std::uint32_t(blocks[8*mid])<id)low=mid+1;else high=mid;}
 if(low==count||std::uint32_t(blocks[8*low])!=id)return false;
 p=location(positions+2*low);for(std::uint32_t i=0;i<mc;++i)if(std::uint32_t(moves[3ULL*i])==id)p=location(moves+3ULL*i+1);return true;
}
inline std::uint64_t distance(Location a,Location b){auto x=std::int64_t(a.x)-b.x,y=std::int64_t(a.y)-b.y;return std::uint64_t(x<0?-x:x)+std::uint64_t(y<0?-y:y);}
inline bool product(std::uint64_t a,std::uint64_t b,std::uint64_t& out){auto wide=static_cast<unsigned __int128>(a)*b;if(wide>>64)return false;out=std::uint64_t(wide);return true;}
inline bool add(std::uint64_t& a,std::uint64_t b){if(b>UINT64_MAX-a)return false;a+=b;return true;}
// Status: 1 range/count, 2 unknown ID, 3 arithmetic, 4 pressure error.
inline Result net_cost(Range member_range,Range connection_range,const std::uint64_t* blocks,const std::uint64_t* positions,std::uint64_t bc,const std::uint32_t* members,std::uint64_t member_count,const std::uint64_t* connections,std::uint64_t cc,const std::uint64_t* lines,std::uint64_t lc,const std::uint64_t* entries,std::uint64_t ec,const std::uint64_t* moves,std::uint32_t mc){
 Result out{};std::uint64_t values[3]{};
 if(bc>UINT64_MAX/8||cc>UINT64_MAX/2||!valid_range(member_range,member_count)||!valid_range(connection_range,cc)){out.status=1;return out;}
 for(std::uint32_t i=0;i<mc;++i){Location p{};if(!position(blocks,positions,bc,moves,mc,std::uint32_t(moves[3ULL*i]),p)){out.status=2;return out;}}
 Location low{},high{};for(std::uint64_t i=0;i<member_range.count;++i){Location p{};if(!position(blocks,positions,bc,moves,mc,members[member_range.offset+i],p)){out.status=2;return out;}
 if(!i)low=high=p;
 if(p.x<low.x)low.x=p.x;
 if(p.y<low.y)low.y=p.y;
 if(p.x>high.x)high.x=p.x;
 if(p.y>high.y)high.y=p.y;
 }
 if(member_range.count)values[0]=distance(low,high);
 for(std::uint64_t i=0;i<connection_range.count;++i){auto index=2*(connection_range.offset+i),ids=connections[index],weight=connections[index+1];Location a{},b{};
 if(!position(blocks,positions,bc,moves,mc,std::uint32_t(ids),a)||!position(blocks,positions,bc,moves,mc,std::uint32_t(ids>>32),b)){out.status=2;return out;}
 auto d=distance(a,b);std::uint64_t weighted=0;if(!product(d,weight,weighted)){out.status=3;return out;}if(!add(values[1],weighted)){out.status=3;return out;}
 auto pressure=tileplace_wire::query(lines,lc,entries,ec,{a,b});if(pressure.status){out.status=4;return out;}if(!add(values[2],pressure.minimum)){out.status=3;return out;}
 }
 for(unsigned i=0;i<3;++i)out.costs[i]=values[i];
 return out;
}
}
