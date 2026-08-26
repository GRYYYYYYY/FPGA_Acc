#include "multiqueue.hpp"

#include <iostream>
#include <vector>

using namespace persistroute;

int main() {
 MultiQueue queue{};
 mq_init(queue);
 for (std::uint32_t i = 0; i < 64; ++i) {
  if (!mq_push(queue, {i, 0, 100 - (i % 7), i})) return 1;
 }
 std::uint32_t active_banks = 0;
 for (std::uint32_t bank = 0; bank < MQ_QUEUES; ++bank) {
  if (queue.size[bank] != 0U) ++active_banks;
 }
 if (active_banks < 2U) return 2;

 std::uint32_t last = 0;
 bool first = true;
 MQEntry entry{};
 std::uint32_t count = 0;
 while (mq_pop(queue, entry)) {
  if (!first && entry.cost_q < last) return 3;
  first = false;
  last = entry.cost_q;
  ++count;
 }
 if (count != 64) return 4;

 std::vector<MQEntry> hbm_data(MQ_QUEUES * 16U);
 std::vector<std::uint32_t> hbm_sizes(MQ_QUEUES);
 hbm_mq_init(hbm_sizes.data());
 for (std::uint32_t i = 0; i < 64; ++i) {
  if (!hbm_mq_push(hbm_data.data(), hbm_sizes.data(), 16U,
                   {i, 0, 100 - (i % 7), i})) {
   return 5;
  }
 }
 active_banks = 0;
 for (std::uint32_t bank = 0; bank < MQ_QUEUES; ++bank) {
  if (hbm_sizes[bank] != 0U) ++active_banks;
 }
 if (active_banks < 2U) return 6;
 first = true;
 count = 0;
 while (hbm_mq_pop(hbm_data.data(), hbm_sizes.data(), 16U, entry)) {
  if (!first && entry.cost_q < last) return 7;
  first = false;
  last = entry.cost_q;
  ++count;
 }
 if (count != 64) return 8;

 std::cout << "multiqueue_tb: PASS\n";
 return 0;
}
