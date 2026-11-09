#pragma once
#include "joint_state.hpp"
#include <filesystem>
#include <utility>
namespace fusionpar::joint {
std::pair<Design,State> read_bundle(const std::filesystem::path&);
void write_state(const State&,const std::filesystem::path&);
}
