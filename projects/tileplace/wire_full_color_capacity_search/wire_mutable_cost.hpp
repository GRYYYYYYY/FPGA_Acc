#pragma once
#include "../hbm_abi/flat_pressure.hpp"
#include "../wire_costs/cost_pair_words.hpp"
#include "../wire_commit/commit_words.hpp"
#include <map>
#include <set>
namespace tileplace_hbm {
class WireMutableCosts {
 FlatPressure pressure_;
 std::vector<Location> positions_;
 std::vector<std::uint64_t> wb_,wp_,wn_,wc_,wl_,we_,wr_;
 std::vector<Block> blocks_;
 std::vector<PrefixLine> lines_;
 std::vector<PrefixEntry> entries_;
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
 explicit WireMutableCosts(const std::vector<std::uint8_t>& bytes):pressure_(bytes) {
  constexpr std::array<std::size_t,13> sizes{64,16,32,32,48,4,16,32,4,32,16,16,4};
  std::array<std::size_t,13> starts{};std::array<std::uint64_t,13> counts{};std::size_t cursor=224;
  for(unsigned i=0;i<13;++i) {counts[i]=read(bytes,24+16*i,8);starts[i]=cursor;cursor+=counts[i]*sizes[i];}
  for(std::uint64_t i=0;i<counts[0];++i) {
   auto id=std::uint32_t(read(bytes,starts[0]+i*64,4));
   if(!block_index_.emplace(id,i).second)throw std::invalid_argument("duplicate block ID");
   Block block{};block.id=id;blocks_.push_back(block);
   auto p=starts[1]+i*16;positions_.push_back({signed32(read(bytes,p,4)),signed32(read(bytes,p+4,4)),signed32(read(bytes,p+8,4)),signed32(read(bytes,p+12,4))});
  }
  for(std::uint64_t i=0;i<counts[9];++i){auto p=starts[9]+i*32;lines_.push_back({signed32(read(bytes,p,4)),signed32(read(bytes,p+4,4)),read(bytes,p+8,8),{read(bytes,p+16,8),read(bytes,p+24,8)}});}
  for(std::uint64_t i=0;i<counts[10];++i){auto p=starts[10]+i*16;entries_.push_back({signed32(read(bytes,p,4)),0,read(bytes,p+8,8)});}
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
  auto words=[&](unsigned section,std::vector<std::uint64_t>& out,unsigned width){
   for(std::uint64_t i=0;i<counts[section];++i)for(unsigned j=0;j<width/8;++j)out.push_back(read(bytes,starts[section]+i*width+j*8,8));
  };
  words(0,wb_,64);words(1,wp_,16);words(4,wn_,48);words(6,wc_,16);words(9,wl_,32);words(10,we_,16);words(11,wr_,16);

 }
 void update_positions(const std::map<std::uint32_t,Location>& changes) {
  if(changes.size()>UINT32_MAX)throw std::length_error("commit count overflow");
  std::vector<std::uint64_t> moves;
  for(const auto& [id,p]:changes)moves.insert(moves.end(),{id,std::uint32_t(p.x)|(std::uint64_t(std::uint32_t(p.y))<<32),std::uint32_t(p.subtile)|(std::uint64_t(std::uint32_t(p.layer))<<32)});
  std::uint64_t record[13]={};record[6]=changes.size();std::uint32_t selected=0;unsigned status;
  auto words=wp_;
  tileplace_wire_commit::commit(record,1,&selected,1,moves.data(),changes.size(),wb_.data(),blocks_.size(),words.data(),status);
  if(status)throw std::invalid_argument("integer position commit rejected");
  auto candidate=positions_;
  for(std::size_t i=0;i<candidate.size();++i)candidate[i]={signed32(words[2*i]),signed32(words[2*i]>>32),signed32(words[2*i+1]),signed32(words[2*i+1]>>32)};
  positions_.swap(candidate);wp_.swap(words);
 }
 const std::vector<Net>& nets() const {return nets_;}
 auto cost_pair(const std::set<std::uint32_t>& touched,const std::map<std::uint32_t,Location>& changes) const {
  if(touched.size()>UINT32_MAX||changes.size()>UINT32_MAX)throw std::overflow_error("array query count overflow");
  std::vector<std::uint32_t> ids(touched.begin(),touched.end());std::vector<std::uint64_t> moves;
  for(const auto& [id,p]:changes){moves.push_back(id);moves.push_back(std::uint32_t(p.x)|(std::uint64_t(std::uint32_t(p.y))<<32));moves.push_back(std::uint32_t(p.subtile)|(std::uint64_t(std::uint32_t(p.layer))<<32));}
  auto result=tileplace_wire_costs::cost_pair_words(wn_.data(),nets_.size(),ids.data(),ids.size(),wb_.data(),wp_.data(),blocks_.size(),members_.data(),members_.size(),wc_.data(),connections_.size(),wl_.data(),lines_.size(),we_.data(),entries_.size(),wr_.data(),routed_.size(),moves.data(),changes.size());
  if(result.status==3)throw std::overflow_error("array cost arithmetic overflow");
  if(result.status)throw std::invalid_argument("array cost query rejected");
  std::array<std::uint64_t,4> before{},after{};
  for(unsigned i=0;i<4;++i){before[i]=result.before[i];after[i]=result.after[i];}
  return std::make_pair(before,after);
 }
};
}
