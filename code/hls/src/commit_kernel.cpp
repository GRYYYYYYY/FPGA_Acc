#include "commit_kernel.hpp"

namespace fpga_acc_hls {

extern "C" void commit_kernel(
    ResourceWord resources[kMaxResources],
    const ReadEntry reads[kMaxEntries],
    const WriteEntry writes[kMaxEntries],
    std::uint32_t resource_count,
    std::uint32_t read_count,
    std::uint32_t write_count,
    CommitResult* result) {
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=resources offset=slave bundle=gmem0 max_read_burst_length=64 max_write_burst_length=64
#pragma HLS INTERFACE m_axi port=reads offset=slave bundle=gmem1 max_read_burst_length=64
#pragma HLS INTERFACE m_axi port=writes offset=slave bundle=gmem2 max_read_burst_length=64
#pragma HLS INTERFACE s_axilite port=resource_count bundle=control
#pragma HLS INTERFACE s_axilite port=read_count bundle=control
#pragma HLS INTERFACE s_axilite port=write_count bundle=control
#pragma HLS INTERFACE s_axilite port=result bundle=control
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
    CommitResult local{0, 0xffffffffU, 0};
    if (resource_count > kMaxResources || read_count > kMaxEntries || write_count > kMaxEntries) {
        *result = local;
        return;
    }

    for (std::uint32_t i = 0; i < read_count; ++i) {
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
        const auto entry = reads[i];
        if (entry.resource_id >= resource_count ||
            resources[entry.resource_id].version != entry.observed_version) {
            local.conflict_resource = entry.resource_id;
            *result = local;
            return;
        }
    }

    for (std::uint32_t i = 0; i < write_count; ++i) {
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
        const auto entry = writes[i];
        if (entry.resource_id >= resource_count) {
            local.conflict_resource = entry.resource_id;
            *result = local;
            return;
        }
        const int next = static_cast<int>(resources[entry.resource_id].occupancy) +
                         static_cast<int>(entry.delta_occupancy);
        if (next < 0 || next > 65535) {
            local.conflict_resource = entry.resource_id;
            *result = local;
            return;
        }
    }

    for (std::uint32_t i = 0; i < write_count; ++i) {
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
        const auto entry = writes[i];
        auto& state = resources[entry.resource_id];
        state.occupancy = static_cast<std::uint16_t>(
            static_cast<int>(state.occupancy) + static_cast<int>(entry.delta_occupancy));
        ++state.version;
        ++local.updated_resources;
    }
    local.committed = 1;
    *result = local;
}

}  // namespace fpga_acc_hls
