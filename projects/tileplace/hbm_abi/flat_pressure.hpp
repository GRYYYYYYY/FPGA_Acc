#pragma once
#include "snapshot_abi.hpp"
#include <algorithm>
#include <array>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>
namespace tileplace_hbm {
class FlatPressure {
 std::vector<PrefixLine> lines_;
 std::vector<PrefixEntry> entries_;
 static std::uint64_t add(std::uint64_t a,std::uint64_t b) {
  if(b>UINT64_MAX-a) throw std::overflow_error("pressure sum overflow");
  return a+b;
 }
 static std::uint64_t read(const std::vector<std::uint8_t>& bytes,std::size_t offset,unsigned width) {
  if(offset>bytes.size() || width>bytes.size()-offset) throw std::invalid_argument("truncated ABI field");
  std::uint64_t value=0;for(unsigned i=0;i<width;++i)value|=std::uint64_t(bytes[offset+i])<<(8*i);return value;
 }
 static std::int32_t signed32(std::uint64_t value) {
  return std::int32_t(value<=INT32_MAX ? std::int64_t(value):std::int64_t(value)-4294967296LL);
 }
 std::uint64_t prefix(const PrefixLine& line,std::int32_t coordinate) const {
  auto begin=entries_.begin()+line.entries.offset,end=begin+line.entries.count;
  auto found=std::lower_bound(begin,end,coordinate,[](const PrefixEntry& e,std::int32_t c){return e.coordinate<c;});
  return found==end?line.total_pressure:found->cumulative_before;
 }
 std::uint64_t segment(int axis,std::int32_t line,std::int32_t a,std::int32_t b) const {
  auto key=std::make_pair(axis,line);
  auto found=std::lower_bound(lines_.begin(),lines_.end(),key,[](const PrefixLine& l,const auto& k){return std::make_pair(l.axis,l.line)<k;});
  if(found==lines_.end() || found->axis!=axis || found->line!=line)return 0;
  return prefix(*found,std::max(a,b))-prefix(*found,std::min(a,b));
 }
public:
 explicit FlatPressure(const std::vector<std::uint8_t>& bytes) {
  if(read(bytes,0,4)!=MAGIC || read(bytes,4,4)!=VERSION)throw std::invalid_argument("ABI identity differs");
  constexpr std::array<std::size_t,13> widths{64,16,32,32,48,4,16,32,4,32,16,16,4};
  std::array<std::size_t,13> starts{};std::array<std::uint64_t,13> counts{};
  std::size_t cursor=224;
  for(unsigned i=0;i<13;++i) {
   auto offset=read(bytes,16+16*i,8);counts[i]=read(bytes,24+16*i,8);starts[i]=cursor;
   if(offset || cursor>bytes.size() || counts[i]>(bytes.size()-cursor)/widths[i])throw std::invalid_argument("invalid ABI section");
   cursor+=std::size_t(counts[i])*widths[i];
  }
  if(cursor!=bytes.size() || counts[0]!=counts[1])throw std::invalid_argument("ABI length/count mismatch");
  for(std::uint64_t i=0;i<counts[10];++i) {
   auto p=starts[10]+i*16;
   if(read(bytes,p+4,4))throw std::invalid_argument("prefix reserved field");
   entries_.push_back({signed32(read(bytes,p,4)),0,read(bytes,p+8,8)});
  }
  for(std::uint64_t i=0;i<counts[9];++i) {
   auto p=starts[9]+i*32;
   PrefixLine line{signed32(read(bytes,p,4)),signed32(read(bytes,p+4,4)),read(bytes,p+8,8),{read(bytes,p+16,8),read(bytes,p+24,8)}};
   if((line.axis!=0 && line.axis!=1) || !line.entries.count || !valid_range(line.entries,entries_.size()))throw std::invalid_argument("invalid prefix line");
   if(!lines_.empty() && std::make_pair(lines_.back().axis,lines_.back().line)>=std::make_pair(line.axis,line.line))throw std::invalid_argument("prefix lines unsorted");
   std::uint64_t last=0;
   for(std::uint64_t j=0;j<line.entries.count;++j) {
    auto index=line.entries.offset+j;const auto& e=entries_[index];
    if((!j && e.cumulative_before) || (j && e.coordinate<=entries_[index-1].coordinate) || e.cumulative_before<last || e.cumulative_before>line.total_pressure)throw std::invalid_argument("prefix index differs");
    last=e.cumulative_before;
   }
   lines_.push_back(line);
  }
 }
 std::uint64_t path(Location a,Location b,bool horizontal_first) const {
  auto dx=std::int64_t(a.x)-b.x,dy=std::int64_t(a.y)-b.y;
  auto base=(std::uint64_t(dx<0?-dx:dx)+std::uint64_t(dy<0?-dy:dy))*65536;
  return add(add(base,segment(0,horizontal_first?a.y:b.y,a.x,b.x)),segment(1,horizontal_first?b.x:a.x,a.y,b.y));
 }
};
}
