#pragma once
#include <cstddef>
#include <cstdint>
#include <type_traits>

namespace tileplace_hbm {
// Version 1 wire records: little-endian fields, offsets/counts in records.
// Host serialization must write fields explicitly; native structs are only a
// compile-time layout contract, never an unchecked reinterpret_cast parser.
constexpr std::uint32_t VERSION=1;
constexpr std::uint32_t MAGIC=0x434c5054; // little-endian bytes: TPLC
struct Location {std::int32_t x,y,subtile,layer;};
struct Range {std::uint64_t offset,count;};
struct Block {
 std::uint32_t id,type_id;
 Location initial;
 Range regions;
 std::int32_t fixed[4];
 std::uint32_t fixed_mask,unit_id;
};
struct Site {Location location;std::uint32_t type_id,reserved[3];};
struct Region {
 std::int32_t xmin,ymin,xmax,ymax,layer_low,layer_high,subtile;
 std::uint32_t reserved;
};
struct Net {std::uint32_t id,reserved[3];Range members,connections;};
struct Connection {std::uint32_t source,sink;std::uint64_t weight;};
struct Unit {Range members;std::uint32_t fixed,reserved[3];};
struct PrefixLine {std::int32_t axis,line;std::uint64_t total_pressure;Range entries;};
struct PrefixEntry {std::int32_t coordinate;std::uint32_t reserved;std::uint64_t cumulative_before;};
struct Header {
 std::uint32_t magic,version;
 std::uint64_t generation;
 Range blocks,positions,sites,regions,nets,net_members,connections;
 Range units,unit_members,prefix_lines,prefix_entries,routed_edges,focus;
};
static_assert(sizeof(Location)==16);
static_assert(sizeof(Range)==16);
static_assert(sizeof(Block)==64 && offsetof(Block,fixed_mask)==56);
static_assert(sizeof(Site)==32 && sizeof(Region)==32);
static_assert(sizeof(Net)==48 && sizeof(Connection)==16 && sizeof(Unit)==32);
static_assert(sizeof(PrefixLine)==32 && sizeof(PrefixEntry)==16);
static_assert(sizeof(Header)==224 && offsetof(Header,blocks)==16);
static_assert(std::is_standard_layout<Block>::value && std::is_trivially_copyable<Header>::value);
inline bool valid_range(Range range,std::uint64_t total) {
 return range.offset<=total && range.count<=total-range.offset;
}
}
