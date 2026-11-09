#pragma once
#include "../hbm_abi/flat_placement.hpp"
#include "../hbm_abi/canonical_snapshot.hpp"
#include "array_mutable_cost.hpp"
#include <memory>
namespace tileplace_hbm {
class ArrayCostState {
 struct Version {
  FlatPlacement placement;
  ArrayMutableCosts costs;
  explicit Version(const std::vector<std::uint8_t>& bytes):placement(bytes),costs(bytes){}
 };
 std::shared_ptr<const Version> current_;
 static std::map<std::uint32_t,Location> convert(const tileplace_snapshot::Positions& positions) {
  std::map<std::uint32_t,Location> result;
  for(const auto& [id,p]:positions)result[id]={p.x,p.y,p.subtile,p.layer};
  return result;
 }
public:
 struct Snapshot {private:friend class ArrayCostState;std::shared_ptr<const Version> value;};
 explicit ArrayCostState(const std::vector<std::uint8_t>& bytes){validate_canonical_snapshot(bytes);current_=std::make_shared<const Version>(bytes);}
 Snapshot snapshot() const {Snapshot saved;saved.value=current_;return saved;}
 void restore(const Snapshot& saved) {
  if(!saved.value)throw std::invalid_argument("empty snapshot");
  current_=saved.value;
 }
 const tileplace_snapshot::Positions& positions() const {return current_->placement.positions();}
 void commit(const tileplace_snapshot::Positions& changes) {
  auto next=std::make_shared<Version>(*current_);
  next->placement.commit(changes);next->costs.update_positions(convert(changes));
  current_=std::move(next);
 }
 auto evaluate(const std::set<std::uint32_t>& nets,const tileplace_snapshot::Positions& changes) const {
  return current_->costs.cost_pair(nets,convert(changes));
 }
};
}
