#pragma once
#include "summary_hbm.hpp"
namespace dieroute {
// Additional owner operation: fetch and atomically register worker/lane.
constexpr std::uint32_t owner_subscribe=6;
constexpr std::uint64_t publisher_queue_exhausted=10;
// Registry words: session, subscribers, pending, queued(0/1), 0,0,0,0.
// Subscriber bit = worker*8+lane. A slot appears at most once in dirty_queue.
// Control: session, dirty_read, dirty_write, 0,0,0,0,0.
// Update record: packet + {lane,slot,version,0,0,0,0,0}; packet serial is
// the producer's update ticket+1. Receiver transport may have its own envelope.
// Completion: command_read,response_write,update_write,commands,updates,
// queue_visits,launch_or_queue_error,session. Status replies use summary ABI.
// Host owns all buffers between launches; no crash-atomic or concurrent DMA
// guarantee. Pending bits clear only after an output queue record is written.
extern "C" void dieroute_owner_publish_hbm(
    const SummaryWord* commands,const std::uint64_t* topology,
    SummaryWord* owners,SummaryWord* registry,std::uint32_t* dirty_queue,
    SummaryWord* responses,SummaryWord* updates,SummaryWord* queue_control,SummaryWord* completion,
    std::uint32_t slots,std::uint32_t lanes,std::uint32_t die,std::uint32_t dies,
    std::uint64_t session,std::uint32_t command_capacity,std::uint32_t response_capacity,
    std::uint32_t update_capacity,std::uint32_t dirty_capacity,
    std::uint64_t command_read,std::uint64_t command_write,
    std::uint64_t response_read,std::uint64_t response_write,
    std::uint64_t update_read,std::uint64_t update_write,
    std::uint32_t max_commands,std::uint32_t max_updates,std::uint32_t max_visits,
    std::uint64_t subscriber_filter);
}
