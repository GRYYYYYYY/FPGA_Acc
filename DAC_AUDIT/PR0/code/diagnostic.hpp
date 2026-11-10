#pragma once
#include "accelerated_pathfinder.hpp"
#include "multiqueue.hpp"
#include <vector>
#include <string>
namespace persistroute {
struct WideResult { uint32_t offset,length,status,read_offset,read_count,reserved; };
struct Observation {
 std::vector<uint8_t> seen;
 std::vector<uint32_t> ids;
 uint64_t calls=0,queue_peak=0,score_calls=0,score_unique=0;
 std::string failure="none";
 uint32_t limit=0xffffffffU;
 void reset(size_t n,uint32_t lim=0xffffffffU){seen.assign(n,0);ids.clear();calls=queue_peak=score_calls=score_unique=0;failure="none";limit=lim;}
};
extern Observation observation;
bool observe_read(uint32_t id);
bool observe_push(MQEntry*,uint32_t*,uint32_t,const MQEntry&);
extern "C" void wide_search(const Node*,const Edge*,const Resource*,const Task*,uint32_t*,ReadEntry*,WideResult*,uint32_t*,uint32_t*,uint32_t*,uint32_t*,uint32_t*,uint32_t*,MQEntry*,uint32_t*,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t,Metrics*);
}
