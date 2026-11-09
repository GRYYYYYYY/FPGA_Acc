#pragma once
#include <cstdint>
namespace dieroute {
// All words are little-endian in external artifacts; each aggregate is 64 B.
struct SummaryWord {std::uint64_t w[8];};
static_assert(sizeof(SummaryWord)==64,"summary AXI word");
enum SummaryOp : std::uint32_t {owner_install=1,owner_fetch=2,shadow_receive=3,shadow_inspect=4,owner_validate=5};
enum SummaryStatus : std::uint64_t {summary_ok=0,summary_duplicate=1,summary_stale=2,summary_bad_packet=3,summary_bad_address=4,summary_bad_role=5,summary_missing=6,summary_compare_failed=7,summary_value_conflict=8,summary_bad_record=9};
// A command is packet + descriptor. descriptor: op|lane<<32, slot,
// expected owner version (install only), 0,0,0,0,0.
// A response is packet + receipt: status, command ticket, op|lane<<32,
// slot, wrote_state, 0,0,0. Completion: new input-read, new output-write,
// count, launch_error, writes, rejected, session, 0.
// Stored summary: session, occupancy, history, version, node|mask<<32,0,0,0.
// Topology slots are immutable {node:u32, full_mask:u8, zero:u24}.
// Queue tickets never wrap. Capacity is a power of two; no mutation/consumption
// occurs without a response credit. Callers hand off ownership between launches.
extern "C" void dieroute_summary_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* shadows,SummaryWord* responses,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,std::uint32_t max_steps);
}
