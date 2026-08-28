#include "accelerated_pathfinder.hpp"

#include <algorithm>
#include <chrono>
#include <future>
#include <limits>
#include <stdexcept>

namespace persistroute {

KernelBatchResult execute_hbm_cmodel_batch(
 const std::vector<Node>& nodes,const std::vector<Edge>& edges,std::vector<Resource>& resources,
 const std::vector<Task>& tasks,const std::vector<std::vector<SearchSeed>>& seeds,bool allow_overuse,std::uint32_t pe_count,
 std::uint32_t queue_depth,std::uint32_t transaction_capacity) {
 KernelBatchResult output;if(tasks.empty())return output;if(seeds.size()!=tasks.size())throw std::invalid_argument("task/seed batch mismatch");
 pe_count=std::max<std::uint32_t>(1,std::min<std::uint32_t>(pe_count,tasks.size()));
 if(queue_depth==0)queue_depth=std::max<std::uint32_t>(256,static_cast<std::uint32_t>((8ULL*nodes.size()+MQ_QUEUES-1)/MQ_QUEUES));
 std::vector<std::vector<Task>> partitions(pe_count);std::vector<std::vector<std::vector<SearchSeed>>> seed_partitions(pe_count);
 for(std::size_t i=0;i<tasks.size();++i){partitions[i%pe_count].push_back(tasks[i]);seed_partitions[i%pe_count].push_back(seeds[i]);}
 auto run_partition=[&](std::size_t pe){KernelBatchResult partial;auto part=partitions[pe];const auto& part_seeds=seed_partitions[pe];
  if(part.empty())return partial;
  const std::uint64_t worst=static_cast<std::uint64_t>(nodes.size())*part.size();
  const std::uint32_t capacity=transaction_capacity?transaction_capacity:static_cast<std::uint32_t>(std::min<std::uint64_t>(worst,0xffffffffULL));
  if(capacity==0||worst>0xffffffffULL)throw std::runtime_error("C-model transaction pool exceeds 32-bit ABI");
  std::vector<std::uint32_t> paths(capacity),distance(nodes.size()),predecessor(nodes.size()),hops(nodes.size()),seen(nodes.size()),closed(nodes.size()),read_epoch(nodes.size()),sizes(MQ_QUEUES);
  std::vector<ReadEntry> reads(capacity);std::vector<PathResult> results(part.size());
  std::size_t seed_count=0;for(const auto& item:part_seeds)seed_count+=item.size();const std::size_t active_queue=static_cast<std::size_t>(MQ_QUEUES)*queue_depth;
  std::vector<MQEntry> queue(active_queue+seed_count);std::size_t seed_cursor=active_queue;
  for(std::size_t i=0;i<part.size();++i){if(part_seeds[i].empty()||part_seeds[i].size()>0xffffffffULL)throw std::runtime_error("invalid search seed list");part[i].reserved=seed_cursor;part[i].epoch=part_seeds[i].size();for(const auto& seed:part_seeds[i])queue[seed_cursor++]={seed.node,INVALID_RESOURCE,0,seed.hops};}
  Metrics metrics{};const auto search_begin=std::chrono::steady_clock::now();
  search_hbm_kernel(nodes.data(),edges.data(),resources.data(),part.data(),paths.data(),reads.data(),results.data(),distance.data(),predecessor.data(),hops.data(),seen.data(),closed.data(),read_epoch.data(),queue.data(),sizes.data(),nodes.size(),edges.size(),part.size(),queue_depth,capacity,&metrics);
  partial.telemetry.search_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-search_begin).count();++partial.telemetry.search_launches;
  partial.search_metrics.expanded+=metrics.expanded;partial.search_metrics.edge_visits+=metrics.edge_visits;partial.search_metrics.failed+=metrics.failed;
  for(std::size_t i=0;i<part.size();++i){KernelCandidate candidate{};candidate.task=tasks[0];candidate.task=part[i];candidate.task.epoch=0;candidate.task.reserved=0;candidate.search_status=results[i].status;candidate.commit_status=results[i].status;
   if(results[i].status==1){const auto& r=results[i];candidate.path.assign(paths.begin()+r.offset,paths.begin()+r.offset+r.length);if(candidate.path.empty())throw std::runtime_error("multi-source kernel omitted attachment");candidate.attachment=candidate.path.front();candidate.path.erase(candidate.path.begin());candidate.reads.assign(reads.begin()+r.read_offset,reads.begin()+r.read_offset+r.read_count);}partial.candidates.push_back(std::move(candidate));}
  return partial;
 };
 std::vector<std::future<KernelBatchResult>> searches;searches.reserve(partitions.size());
 for(std::size_t pe=0;pe<partitions.size();++pe)if(!partitions[pe].empty())searches.push_back(std::async(std::launch::async,run_partition,pe));
 for(auto& pending:searches){KernelBatchResult partial=pending.get();output.telemetry.search_ns=std::max(output.telemetry.search_ns,partial.telemetry.search_ns);output.telemetry.search_launches+=partial.telemetry.search_launches;output.search_metrics.expanded+=partial.search_metrics.expanded;output.search_metrics.edge_visits+=partial.search_metrics.edge_visits;output.search_metrics.failed+=partial.search_metrics.failed;output.candidates.insert(output.candidates.end(),std::make_move_iterator(partial.candidates.begin()),std::make_move_iterator(partial.candidates.end()));}
 std::sort(output.candidates.begin(),output.candidates.end(),[](const auto& a,const auto& b){return std::tie(a.task.priority,a.task.id)<std::tie(b.task.priority,b.task.id);});
 std::vector<Task> commit_tasks;std::vector<std::uint32_t> paths;std::vector<ReadEntry> reads;std::vector<PathResult> results;
 for(const auto& c:output.candidates){PathResult r{};r.offset=paths.size();r.read_offset=reads.size();r.length=c.path.size();r.read_count=c.reads.size();r.status=c.search_status;if(r.length!=c.path.size()||r.read_count!=c.reads.size())throw std::runtime_error("kernel transaction exceeds 16-bit record");commit_tasks.push_back(c.task);paths.insert(paths.end(),c.path.begin(),c.path.end());reads.insert(reads.end(),c.reads.begin(),c.reads.end());results.push_back(r);}
 const std::size_t capacity=std::max<std::size_t>({paths.size(),reads.size(),1});paths.resize(capacity);reads.resize(capacity);Metrics metrics{};
 const auto commit_begin=std::chrono::steady_clock::now();commit_hbm_kernel(resources.data(),resources.data(),resources.data(),resources.data(),commit_tasks.data(),paths.data(),reads.data(),results.data(),resources.size(),commit_tasks.size(),capacity,allow_overuse?1U:0U,&metrics);
 output.telemetry.commit_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now()-commit_begin).count();output.telemetry.commit_launches=1;
 output.commit_metrics=metrics;for(std::size_t i=0;i<output.candidates.size();++i)output.candidates[i].commit_status=results[i].status;
 return output;
}

} // namespace persistroute
