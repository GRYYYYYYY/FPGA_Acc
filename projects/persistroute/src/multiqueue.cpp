#include "multiqueue.hpp"

namespace persistroute {
namespace {

bool before(const MQEntry& a, const MQEntry& b) {
 return a.cost_q < b.cost_q ||
        (a.cost_q == b.cost_q &&
         (a.tie < b.tie || (a.tie == b.tie && a.node < b.node)));
}

std::uint32_t queue_bank(const MQEntry& entry) {
 // The callers deliberately use node as the deterministic tie breaker.  A
 // simple node^tie hash would therefore collapse every entry into bank zero.
 std::uint32_t mixed = entry.node * 0x9e3779b9U;
 mixed ^= entry.tie * 0x85ebca6bU;
 mixed ^= mixed >> 16;
 mixed *= 0x7feb352dU;
 mixed ^= mixed >> 15;
 return mixed & (MQ_QUEUES - 1U);
}

}  // namespace

void mq_init(MultiQueue& queue) {
 for (std::uint32_t i = 0; i < MQ_QUEUES; ++i) queue.size[i] = 0;
}

bool mq_push(MultiQueue& queue, const MQEntry& entry) {
 const std::uint32_t bank = queue_bank(entry);
 const std::uint16_t old_size = queue.size[bank];
 if (old_size >= MQ_DEPTH) return false;
 queue.size[bank] = static_cast<std::uint16_t>(old_size + 1U);
 std::uint16_t pos = old_size;
 while (pos > 0) {
  const std::uint16_t parent = static_cast<std::uint16_t>((pos - 1U) / 2U);
  if (!before(entry, queue.data[bank][parent])) break;
  queue.data[bank][pos] = queue.data[bank][parent];
  pos = parent;
 }
 queue.data[bank][pos] = entry;
 return true;
}

bool mq_pop(MultiQueue& queue, MQEntry& out) {
 std::uint32_t best = MQ_QUEUES;
 for (std::uint32_t bank = 0; bank < MQ_QUEUES; ++bank) {
  if (queue.size[bank] != 0U &&
      (best == MQ_QUEUES || before(queue.data[bank][0], queue.data[best][0]))) {
   best = bank;
  }
 }
 if (best == MQ_QUEUES) return false;
 out = queue.data[best][0];
 const std::uint16_t new_size = static_cast<std::uint16_t>(queue.size[best] - 1U);
 queue.size[best] = new_size;
 const MQEntry tail = queue.data[best][new_size];
 std::uint16_t pos = 0;
 while (true) {
  const std::uint16_t left = static_cast<std::uint16_t>(pos * 2U + 1U);
  const std::uint16_t right = static_cast<std::uint16_t>(left + 1U);
  if (left >= new_size) break;
  const std::uint16_t child =
      (right < new_size && before(queue.data[best][right], queue.data[best][left]))
          ? right
          : left;
  if (!before(queue.data[best][child], tail)) break;
  queue.data[best][pos] = queue.data[best][child];
  pos = child;
 }
 if (new_size != 0U) queue.data[best][pos] = tail;
 return true;
}

void hbm_mq_init(std::uint32_t sizes[MQ_QUEUES]) {
 for (std::uint32_t i = 0; i < MQ_QUEUES; ++i) sizes[i] = 0;
}

bool hbm_mq_push(MQEntry* data, std::uint32_t sizes[MQ_QUEUES],
                 std::uint32_t depth, const MQEntry& entry) {
 if (depth == 0U) return false;
 const std::uint32_t bank = queue_bank(entry);
 // Keep m_axi-backed array accesses as explicit scalar loads/stores.  Vitis
 // HLS 2022.2's co-simulation C model mishandles references and post-increment
 // expressions bound directly to these elements.
 const std::uint32_t old_size = sizes[bank];
 if (old_size >= depth) return false;
 sizes[bank] = old_size + 1U;
 std::uint32_t pos = old_size;
 while (pos > 0U) {
  const std::uint32_t parent = (pos - 1U) / 2U;
  const MQEntry parent_entry = data[bank * depth + parent];
  if (!before(entry, parent_entry)) break;
  data[bank * depth + pos] = parent_entry;
  pos = parent;
 }
 data[bank * depth + pos] = entry;
 return true;
}

bool hbm_mq_pop(MQEntry* data, std::uint32_t sizes[MQ_QUEUES],
                std::uint32_t depth, MQEntry& out) {
 if (depth == 0U) return false;
 std::uint32_t best = MQ_QUEUES;
 for (std::uint32_t bank = 0; bank < MQ_QUEUES; ++bank) {
  const std::uint32_t bank_size = sizes[bank];
  if (bank_size != 0U &&
      (best == MQ_QUEUES || before(data[bank * depth], data[best * depth]))) {
   best = bank;
  }
 }
 if (best == MQ_QUEUES) return false;
 out = data[best * depth];
 const std::uint32_t new_size = sizes[best] - 1U;
 sizes[best] = new_size;
 const MQEntry tail = data[best * depth + new_size];
 std::uint32_t pos = 0;
 while (true) {
  const std::uint32_t left = pos * 2U + 1U;
  const std::uint32_t right = left + 1U;
  if (left >= new_size) break;
  const MQEntry left_entry = data[best * depth + left];
  std::uint32_t child = left;
  MQEntry child_entry = left_entry;
  if (right < new_size) {
   const MQEntry right_entry = data[best * depth + right];
   if (before(right_entry, left_entry)) {
    child = right;
    child_entry = right_entry;
   }
  }
  if (!before(child_entry, tail)) break;
  data[best * depth + pos] = child_entry;
  pos = child;
 }
 if (new_size != 0U) data[best * depth + pos] = tail;
 return true;
}

}  // namespace persistroute
