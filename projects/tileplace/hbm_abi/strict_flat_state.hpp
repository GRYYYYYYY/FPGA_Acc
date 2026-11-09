#pragma once
#include "flat_state.hpp"
#include "canonical_snapshot.hpp"
namespace tileplace_hbm {
class StrictFlatState:public FlatState {
 static const std::vector<std::uint8_t>& checked(const std::vector<std::uint8_t>& bytes) {
  validate_canonical_snapshot(bytes);return bytes;
 }
public:
 explicit StrictFlatState(const std::vector<std::uint8_t>& bytes):FlatState(checked(bytes)){}
};
}
