#pragma once
#include "accelerated_pathfinder.hpp"
#include "wide_costs.hpp"
#include <memory>
#include <stdexcept>
#include <unordered_map>

namespace dieroute {
struct RRStateOverride {
    persistroute::Resource resource;
    WideCost cost;
};
using RRStateOverlay = std::unordered_map<std::uint32_t,RRStateOverride>;

// A borrowed read view, not an independently writable state replica. The caller
// must keep the base arrays alive and unchanged for the whole read phase. Worker
// joins precede every authoritative write in SpeculativeBackend. Only boundary
// summaries are copied; their net owner is taken from the current base snapshot.
class RRStateView {
    const std::vector<persistroute::Resource>* resources_;
    const std::vector<WideCost>* costs_;
    std::shared_ptr<const RRStateOverlay> overlay_;
public:
    explicit RRStateView(const std::vector<persistroute::Resource>& resources,
                         const std::vector<WideCost>* costs=nullptr,
                         std::shared_ptr<const RRStateOverlay> overlay={})
        :resources_(&resources),costs_(costs),overlay_(std::move(overlay)) {
        if(costs_&&costs_->size()!=resources.size())throw std::invalid_argument("RR view cost coverage");
        if(overlay_)for(const auto& [n,value]:*overlay_)
            if(n>=resources.size()||value.resource.owner!=resources[n].owner)
                throw std::invalid_argument("RR overlay bounds/authoritative owner mismatch");
    }
    std::size_t size()const{return resources_->size();}
    const persistroute::Resource& resource(std::uint32_t n)const {
        if(overlay_){auto it=overlay_->find(n);if(it!=overlay_->end())return it->second.resource;}
        return resources_->at(n);
    }
    const WideCost* cost(std::uint32_t n)const {
        if(overlay_){auto it=overlay_->find(n);if(it!=overlay_->end())return &it->second.cost;}
        return costs_?&costs_->at(n):nullptr;
    }
    std::size_t overlay_records()const{return overlay_?overlay_->size():0;}
    const persistroute::Resource* borrowed_data()const{return resources_->data();}
};
} // namespace dieroute
