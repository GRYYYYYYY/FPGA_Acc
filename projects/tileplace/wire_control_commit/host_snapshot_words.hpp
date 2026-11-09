#pragma once
#include "full_color_words.hpp"
#include "../hbm_abi/canonical_snapshot.hpp"
#include <vector>
namespace tileplace_wire_control_commit {
// Own the complete strict snapshot data planes required by full_color, including
// connection, pressure and routed feedback arrays absent from placement metadata.
class HostSnapshotWords {
 std::vector<std::uint64_t> words_[13];
 std::vector<std::uint32_t> ids_[13];
 std::uint64_t counts_[13]{};
 static std::uint64_t read(const std::vector<std::uint8_t>& bytes,std::size_t at,unsigned size){
  if(at>bytes.size()||size>bytes.size()-at)throw std::invalid_argument("truncated snapshot word");
  std::uint64_t value=0;for(unsigned j=0;j<size;++j)value|=std::uint64_t(bytes[at+j])<<(8*j);return value;
 }
public:
 explicit HostSnapshotWords(const std::vector<std::uint8_t>& bytes){
  tileplace_hbm::validate_canonical_snapshot(bytes);
  const unsigned widths[13]={64,16,32,32,48,4,16,32,4,32,16,16,4};std::size_t offset=224;
  for(unsigned section=0;section<13;++section){auto count=read(bytes,24+16*section,8);counts_[section]=count;
   for(std::uint64_t i=0;i<count;++i){auto start=offset+i*widths[section];
    if(widths[section]==4)ids_[section].push_back(read(bytes,start,4));
    else for(unsigned j=0;j<widths[section];j+=8)words_[section].push_back(read(bytes,start+j,8));
   }
   offset+=count*widths[section];
  }
 }
 // Borrowed arrays remain valid until this owner is destroyed or modified.
 // Caller fills guards, weights, color/page config and external forbidden.
 ColorInput input(){
  ColorInput in{};in.blocks=words_[0].data();in.positions=words_[1].data();in.sites=words_[2].data();in.regions=words_[3].data();in.nets=words_[4].data();in.net_members=ids_[5].data();in.connections=words_[6].data();in.units=words_[7].data();in.unit_members=ids_[8].data();in.lines=words_[9].data();in.entries=words_[10].data();in.routed=words_[11].data();in.focus=ids_[12].data();
  in.block_count=counts_[0];in.site_count=counts_[2];in.region_count=counts_[3];in.net_count=counts_[4];in.net_member_count=counts_[5];in.connection_count=counts_[6];in.unit_count=counts_[7];in.unit_member_count=counts_[8];in.line_count=counts_[9];in.entry_count=counts_[10];in.routed_count=counts_[11];in.focus_count=counts_[12];return in;
 }
};
}
