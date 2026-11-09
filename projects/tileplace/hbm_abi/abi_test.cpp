#include "snapshot_abi.hpp"
#include <stdexcept>
int main() {
 using namespace tileplace_hbm;
 if(!valid_range({UINT64_MAX,0},UINT64_MAX) || valid_range({UINT64_MAX,1},UINT64_MAX) ||
    valid_range({10,UINT64_MAX},20) || !valid_range({0,0},0)) throw std::runtime_error("range overflow");
}
