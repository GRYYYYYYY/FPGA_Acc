#pragma once
#include <cstdint>
namespace persistroute {
constexpr std::uint32_t MQ_QUEUES=8,MQ_DEPTH=256,MQ_MAX_PE=16;
struct MQEntry {std::uint32_t node;std::uint32_t predecessor;std::uint32_t cost_q;std::uint32_t tie;};
struct MultiQueue {MQEntry data[MQ_QUEUES][MQ_DEPTH];std::uint16_t size[MQ_QUEUES];};
void mq_init(MultiQueue& q);
bool mq_push(MultiQueue& q,const MQEntry& entry);
bool mq_pop(MultiQueue& q,MQEntry& entry);
void hbm_mq_init(std::uint32_t sizes[MQ_QUEUES]);
bool hbm_mq_push(MQEntry* data,std::uint32_t sizes[MQ_QUEUES],std::uint32_t depth,const MQEntry& entry);
bool hbm_mq_pop(MQEntry* data,std::uint32_t sizes[MQ_QUEUES],std::uint32_t depth,MQEntry& entry);
}
