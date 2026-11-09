#pragma once
#include "flat_pressure.hpp"
#include <map>
#include <set>
namespace tileplace_hbm {
class FlatTrialCosts {
 FlatPressure pressure_;
 std::vector<Location> positions_;
 std::map<std::uint32_t,std::size_t> block_index_;
 std::vector<std::uint32_t> members_;
 std::vector<Connection> connections_;
 std::vector<Net> nets_;
 std::vector<Connection> routed_;
 static std::uint64_t read(const std::vector<std::uint8_t>& b,std::size_t p,unsigned n) {
  if(p>b.size() || n>b.size()-p)throw std::invalid_argument("truncated field");
  std::uint64_t v=0;for(unsigned i=0;i<n;++i)v|=std::uint64_t(b[p+i])<<(8*i);return v;
 }
 static std::int32_t signed32(std::uint64_t v) {return std::int32_t(v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL);}
 static std::uint64_t add(std::uint64_t a,std::uint64_t b) {
  if(b>UINT64_MAX-a)throw std::overflow_error("net cost sum overflow");
  return a+b;
 }
 static std::uint64_t multiply(std::uint64_t a,std::uint64_t b) {
  if(a && b>UINT64_MAX/a)throw std::overflow_error("net cost product overflow");
  return a*b;
 }
 static std::uint64_t distance(Location a,Location b) {
  auto x=std::int64_t(a.x)-b.x,y=std::int64_t(a.y)-b.y;
  return std::uint64_t(x<0?-x:x)+std::uint64_t(y<0?-y:y);
 }
 Location position(std::uint32_t id,const std::map<std::uint32_t,Location>& changes={}) const {
  auto found=changes.find(id);return found==changes.end()?positions_.at(block_index_.at(id)):found->second;
 }
public:
 explicit FlatTrialCosts(const std::vector<std::uint8_t>& bytes):pressure_(bytes) {
  constexpr std::array<std::size_t,13> sizes{64,16,32,32,48,4,16,32,4,32,16,16,4};
  std::array<std::size_t,13> starts{};std::array<std::uint64_t,13> counts{};std::size_t cursor=224;
  for(unsigned i=0;i<13;++i) {counts[i]=read(bytes,24+16*i,8);starts[i]=cursor;cursor+=counts[i]*sizes[i];}
  for(std::uint64_t i=0;i<counts[0];++i) {
   auto id=std::uint32_t(read(bytes,starts[0]+i*64,4));
   if(!block_index_.emplace(id,i).second)throw std::invalid_argument("duplicate block ID");
   auto p=starts[1]+i*16;positions_.push_back({signed32(read(bytes,p,4)),signed32(read(bytes,p+4,4)),signed32(read(bytes,p+8,4)),signed32(read(bytes,p+12,4))});
  }
  for(std::uint64_t i=0;i<counts[5];++i) {
   auto id=std::uint32_t(read(bytes,starts[5]+i*4,4));if(!block_index_.count(id))throw std::invalid_argument("unknown net member");members_.push_back(id);
  }
  for(std::uint64_t i=0;i<counts[6];++i) {
   auto p=starts[6]+i*16;Connection c{std::uint32_t(read(bytes,p,4)),std::uint32_t(read(bytes,p+4,4)),read(bytes,p+8,8)};
   if(!block_index_.count(c.source)||!block_index_.count(c.sink))throw std::invalid_argument("unknown net endpoint");
   connections_.push_back(c);
  }
  for(std::uint64_t i=0;i<counts[11];++i) {
   auto p=starts[11]+i*16;Connection c{std::uint32_t(read(bytes,p,4)),std::uint32_t(read(bytes,p+4,4)),read(bytes,p+8,8)};
   if(!block_index_.count(c.source)||!block_index_.count(c.sink)||c.source>=c.sink||!c.weight)throw std::invalid_argument("invalid routed feedback");
   routed_.push_back(c);
  }
  std::set<std::uint32_t> ids;
  for(std::uint64_t i=0;i<counts[4];++i) {
   auto p=starts[4]+i*48;Net net{};net.id=read(bytes,p,4);
   if(!ids.insert(net.id).second || read(bytes,p+4,4)||read(bytes,p+8,4)||read(bytes,p+12,4))throw std::invalid_argument("invalid net metadata");
   net.members={read(bytes,p+16,8),read(bytes,p+24,8)};net.connections={read(bytes,p+32,8),read(bytes,p+40,8)};
   if(!valid_range(net.members,members_.size())||!valid_range(net.connections,connections_.size()))throw std::invalid_argument("net CSR range overflow");
   nets_.push_back(net);
  }
 }
 const std::vector<Net>& nets() const {return nets_;}
 std::array<std::uint64_t,3> cost(const Net& net,const std::map<std::uint32_t,Location>& changes={}) const {
  std::array<std::uint64_t,3> result{};
  if(net.members.count) {
   auto p=position(members_.at(net.members.offset),changes);auto low=p,high=p;
   for(std::uint64_t j=0;j<net.members.count;++j) {
    p=position(members_.at(net.members.offset+j),changes);low.x=std::min(low.x,p.x);low.y=std::min(low.y,p.y);high.x=std::max(high.x,p.x);high.y=std::max(high.y,p.y);
   }
   result[0]=distance(low,high);
  }
  for(std::uint64_t j=0;j<net.connections.count;++j) {
   auto c=connections_.at(net.connections.offset+j);auto a=position(c.source,changes),b=position(c.sink,changes);
   result[1]=add(result[1],multiply(c.weight,distance(a,b)));
   result[2]=add(result[2],std::min(pressure_.path(a,b,true),pressure_.path(a,b,false)));
  }
  return result;
 }
 std::pair<std::array<std::uint64_t,4>,std::array<std::uint64_t,4>> cost_pair(
   const std::set<std::uint32_t>& touched,const std::map<std::uint32_t,Location>& changes) const {
  for(const auto& [id,p]:changes) {(void)p;if(!block_index_.count(id))throw std::invalid_argument("unknown changed block");}
  std::array<std::uint64_t,4> before{},after{};std::size_t found=0;
  for(const auto& net:nets_) if(touched.count(net.id)) {
   ++found;auto a=cost(net),b=cost(net,changes);
   before[0]=add(before[0],a[0]);after[0]=add(after[0],b[0]);
   before[1]=add(before[1],a[1]);after[1]=add(after[1],b[1]);
   before[3]=add(before[3],a[2]);after[3]=add(after[3],b[2]);
  }
  if(found!=touched.size())throw std::invalid_argument("unknown touched net");
  for(const auto& c:routed_) if(changes.count(c.source)||changes.count(c.sink)) {
   before[2]=add(before[2],multiply(c.weight,distance(position(c.source),position(c.sink))));
   after[2]=add(after[2],multiply(c.weight,distance(position(c.source,changes),position(c.sink,changes))));
  }
  return {before,after};
 }
};
}
