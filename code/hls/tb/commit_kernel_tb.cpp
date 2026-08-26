#include "commit_kernel.hpp"

#include <iostream>

using namespace fpga_acc_hls;

int main() {
    static ResourceWord resources[kMaxResources]{};
    static ReadEntry reads[kMaxEntries]{};
    static WriteEntry writes[kMaxEntries]{};
    resources[3] = {0, 1, 4};
    resources[7] = {1, 2, 9};
    reads[0] = {3, 4};
    reads[1] = {7, 9};
    writes[0] = {3, 1, 0};
    writes[1] = {7, -1, 0};
    CommitResult result{};

    commit_kernel(resources, reads, writes, 16, 2, 2, &result);
    if (!result.committed || resources[3].occupancy != 1 ||
        resources[7].occupancy != 0 || resources[3].version != 5 ||
        resources[7].version != 10) {
        std::cerr << "commit case failed\n";
        return 1;
    }

    reads[0] = {3, 4};  // stale version: current version is 5
    writes[0] = {3, -1, 0};
    const auto before = resources[3];
    commit_kernel(resources, reads, writes, 16, 1, 1, &result);
    if (result.committed || result.conflict_resource != 3 ||
        resources[3].occupancy != before.occupancy ||
        resources[3].version != before.version) {
        std::cerr << "conflict case failed\n";
        return 1;
    }

    std::cout << "commit_kernel_tb: PASS\n";
    return 0;
}
