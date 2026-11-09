#pragma once
#include "flat_placement.hpp"
namespace tileplace_hbm {
// Complete container/record checks precede the existing layout/net validators.
inline void validate_canonical_snapshot(const std::vector<std::uint8_t>& bytes) {
 FlatPlacement semantic(bytes);(void)semantic;
 auto read=[&](std::size_t p,unsigned n) {
  if(p>bytes.size()||n>bytes.size()-p)throw std::invalid_argument("truncated canonical field");
  std::uint64_t value=0;for(unsigned i=0;i<n;++i)value|=std::uint64_t(bytes[p+i])<<(8*i);return value;
 };
 constexpr std::array<std::size_t,13> widths{64,16,32,32,48,4,16,32,4,32,16,16,4};
 std::array<std::size_t,13> starts{};std::array<std::uint64_t,13> counts{};std::size_t cursor=224;
 for(unsigned i=0;i<13;++i){counts[i]=read(24+16*i,8);starts[i]=cursor;cursor+=counts[i]*widths[i];}
 auto partition=[&](unsigned owners,unsigned target,unsigned field) {
  std::uint64_t next=0;
  for(std::uint64_t i=0;i<counts[owners];++i){auto p=starts[owners]+i*widths[owners]+field;auto offset=read(p,8),count=read(p+8,8);
   if(offset!=next||!valid_range({offset,count},counts[target]))throw std::invalid_argument("CSR partition differs");
   next+=count;
  }
  if(next!=counts[target])throw std::invalid_argument("unreferenced CSR records");
 };
 partition(0,3,24);partition(4,5,16);partition(4,6,32);partition(7,8,0);partition(9,10,16);
 auto ascending_ids=[&](unsigned section){std::uint64_t last=0;
  for(std::uint64_t i=0;i<counts[section];++i){auto id=read(starts[section]+i*widths[section],4);if(i&&id<=last)throw std::invalid_argument("noncanonical ID order");last=id;}
 };
 ascending_ids(0);ascending_ids(4);ascending_ids(12);
 auto initial_bytes=bytes;
 for(std::uint64_t i=0;i<counts[0];++i){auto p=starts[0]+64*i;auto mask=read(p+56,4);
  for(unsigned j=0;j<4;++j)if(!(mask&(1<<j))&&read(p+40+4*j,4))throw std::invalid_argument("noncanonical unused fixed coordinate");
  for(unsigned j=0;j<16;++j)initial_bytes[starts[1]+16*i+j]=bytes[p+8+j];
 }
 FlatPlacement initial_layout(initial_bytes);(void)initial_layout;
 std::array<std::int64_t,4> previous_site{};
 for(std::uint64_t i=0;i<counts[2];++i){std::array<std::int64_t,4> key{};
  for(unsigned j=0;j<4;++j){auto v=read(starts[2]+32*i+4*j,4);key[j]=v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL;}
  if(i&&key<=previous_site)throw std::invalid_argument("sites unsorted");
  previous_site=key;
 }
 for(std::uint64_t i=0;i<counts[4];++i){auto p=starts[4]+i*48;auto offset=read(p+16,8),count=read(p+24,8);std::set<std::uint32_t> members;
  std::uint64_t last=0;
  for(std::uint64_t j=0;j<count;++j){auto id=read(starts[5]+4*(offset+j),4);if(j&&id<=last)throw std::invalid_argument("net members not unique/sorted");last=id;members.insert(id);}
  auto c=read(p+32,8),n=read(p+40,8);
  for(std::uint64_t j=0;j<n;++j){auto q=starts[6]+16*(c+j);if(!members.count(read(q,4))||!members.count(read(q+4,4)))throw std::invalid_argument("connection outside net");}
 }
 std::pair<std::uint64_t,std::uint64_t> last{};
 for(std::uint64_t i=0;i<counts[11];++i){auto p=starts[11]+16*i;auto key=std::make_pair(read(p,4),read(p+4,4));
  if(i&&key<=last)throw std::invalid_argument("routed feedback duplicate or unsorted");
  last=key;
 }
 for(std::uint64_t i=0;i<counts[7];++i){auto p=starts[7]+32*i;auto offset=read(p,8),count=read(p+8,8);std::uint64_t last_id=0;
  for(std::uint64_t j=0;j<count;++j){auto id=read(starts[8]+4*(offset+j),4);if(j&&id<=last_id)throw std::invalid_argument("unit members unsorted");last_id=id;}
 }
}
}
