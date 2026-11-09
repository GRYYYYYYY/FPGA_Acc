#pragma once
#include "canonical_snapshot.hpp"
#include "callback_proposals.hpp"
#include "../cpp_snapshot/placement.hpp"
namespace tileplace_hbm {
class FlatSearchMetadata {
 tileplace_snapshot::PlacementConstraints constraints_;
 tileplace_snapshot::Positions positions_;
 std::vector<tileplace_snapshot::Unit> units_;
 std::set<tileplace_snapshot::Unit> fixed_;
 std::vector<tileplace_snapshot::Net> nets_;
 std::vector<std::uint32_t> net_ids_;
 std::set<std::uint32_t> focus_;
 static std::uint64_t read(const std::vector<std::uint8_t>& b,std::size_t p,unsigned n) {
  if(p>b.size()||n>b.size()-p)throw std::invalid_argument("truncated field");
  std::uint64_t value=0;for(unsigned i=0;i<n;++i)value|=std::uint64_t(b[p+i])<<(8*i);return value;
 }
 static std::int32_t integer(std::uint64_t v) {return std::int32_t(v<=INT32_MAX?std::int64_t(v):std::int64_t(v)-4294967296LL);}
public:
 explicit FlatSearchMetadata(const std::vector<std::uint8_t>& bytes) {
  validate_canonical_snapshot(bytes);
  constexpr std::array<std::size_t,13> widths{64,16,32,32,48,4,16,32,4,32,16,16,4};
  std::array<std::size_t,13> starts{};std::array<std::uint64_t,13> counts{};std::size_t cursor=224;
  for(unsigned i=0;i<13;++i){starts[i]=cursor;counts[i]=read(bytes,24+16*i,8);cursor+=counts[i]*widths[i];}
  auto point=[&](std::size_t p){return tileplace_snapshot::Point{integer(read(bytes,p,4)),integer(read(bytes,p+4,4)),integer(read(bytes,p+8,4)),integer(read(bytes,p+12,4))};};
  std::vector<tileplace_snapshot::Region> regions;
  for(std::uint64_t i=0;i<counts[3];++i) {
   auto p=starts[3]+32*i;tileplace_snapshot::Region r{integer(read(bytes,p,4)),integer(read(bytes,p+4,4)),integer(read(bytes,p+8,4)),integer(read(bytes,p+12,4)),integer(read(bytes,p+16,4)),integer(read(bytes,p+20,4)),integer(read(bytes,p+24,4))};
   if(read(bytes,p+28,4)||r.xmin>r.xmax||r.ymin>r.ymax||r.layer_low>r.layer_high||r.subtile<-1)throw std::invalid_argument("invalid region");
   regions.push_back(r);
  }
  std::map<std::uint32_t,std::uint32_t> unit_ids;
  for(std::uint64_t i=0;i<counts[0];++i) {
   auto p=starts[0]+64*i;auto id=std::uint32_t(read(bytes,p,4));auto mask=read(bytes,p+56,4);
   auto offset=read(bytes,p+24,8),count=read(bytes,p+32,8);
   if((mask&~0x8000000fULL)||!valid_range({offset,count},regions.size())||(!(mask&0x80000000)&&count))throw std::invalid_argument("invalid block restriction");
   tileplace_snapshot::Block block{std::to_string(read(bytes,p+4,4)),std::nullopt,{}};
   if(mask&0x80000000)block.regions=std::vector<tileplace_snapshot::Region>(regions.begin()+offset,regions.begin()+offset+count);
   for(unsigned j=0;j<4;++j)if(mask&(1<<j))block.fixed[j]=integer(read(bytes,p+40+4*j,4));
   constraints_.blocks[id]=block;constraints_.reference[id]=point(p+8);positions_[id]=point(starts[1]+16*i);unit_ids[id]=read(bytes,p+60,4);
  }
  for(std::uint64_t i=0;i<counts[2];++i) {
   auto p=starts[2]+32*i;
   if(read(bytes,p+20,4)||read(bytes,p+24,4)||read(bytes,p+28,4)||!constraints_.sites.emplace(point(p),std::to_string(read(bytes,p+16,4))).second)throw std::invalid_argument("invalid site");
  }
  std::set<std::uint32_t> owned;
  for(std::uint64_t i=0;i<counts[7];++i) {
   auto p=starts[7]+32*i;Range r{read(bytes,p,8),read(bytes,p+8,8)};auto fixed=read(bytes,p+16,4);
   if(!r.count||!valid_range(r,counts[8])||fixed>1||read(bytes,p+20,4)||read(bytes,p+24,4)||read(bytes,p+28,4))throw std::invalid_argument("invalid unit");
   std::vector<std::uint32_t> members;
   for(std::uint64_t j=0;j<r.count;++j) {
    auto id=std::uint32_t(read(bytes,starts[8]+4*(r.offset+j),4));
    if(!owned.insert(id).second||!unit_ids.count(id)||unit_ids.at(id)!=i)throw std::invalid_argument("unit ownership differs");
    if(!fixed)for(const auto& f:constraints_.blocks.at(id).fixed)if(f)throw std::invalid_argument("fixed block in movable unit");
    members.push_back(id);
   }
   units_.push_back(members);if(fixed)fixed_.insert(members);
   if(members.size()>1)constraints_.macros.push_back(members);
  }
  if(owned.size()!=positions_.size())throw std::invalid_argument("unowned blocks");
  for(std::uint64_t i=0;i<counts[12];++i)if(!positions_.count(read(bytes,starts[12]+4*i,4)))throw std::invalid_argument("unknown focus block");
  for(std::uint64_t i=0;i<counts[4];++i){
   auto p=starts[4]+48*i;tileplace_snapshot::Net net;
   net_ids_.push_back(read(bytes,p,4));
   auto offset=read(bytes,p+16,8),count=read(bytes,p+24,8);
   for(std::uint64_t j=0;j<count;++j)net.members.push_back(read(bytes,starts[5]+4*(offset+j),4));
   nets_.push_back(std::move(net));
  }
  for(std::uint64_t i=0;i<counts[12];++i)focus_.insert(read(bytes,starts[12]+4*i,4));
  if(!constraints_.valid(positions_))throw std::invalid_argument("illegal snapshot placement");
 }
 const auto& constraints() const{return constraints_;}
 const auto& units() const{return units_;}
 const auto& fixed() const{return fixed_;}
 const auto& nets() const{return nets_;}
 const auto& net_ids() const{return net_ids_;}
 const auto& focus() const{return focus_;}
 const tileplace_snapshot::Positions& positions() const {return positions_;}
 void commit(const tileplace_snapshot::Positions& changes) {
  auto candidate=positions_;for(const auto& [id,p]:changes)candidate.at(id)=p;
  if(!constraints_.valid(candidate))throw std::invalid_argument("illegal placement commit");
  positions_=std::move(candidate);
 }
};
}
