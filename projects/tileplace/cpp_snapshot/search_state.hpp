#pragma once
#include "placement.hpp"
#include <memory>

namespace tileplace_snapshot {
struct Feedback {
    PressureSnapshot pressure;
    std::vector<Connection> routed;
    std::set<std::uint32_t> focus;
};

// A transaction owns a complete immutable state version. Rejection restores
// placement and feedback together, including after a partially applied refresh.
class SearchState {
    struct Version {
        Positions positions;
        std::shared_ptr<const Feedback> feedback;
    };
    std::vector<Net> nets_;
    std::shared_ptr<const Version> current_, saved_;
    std::map<std::size_t,Cost> cache_;
    std::shared_ptr<const PlacementConstraints> constraints_;
    void install(std::shared_ptr<const Version> next) {
        current_=std::move(next); cache_.clear();
    }
    void validate(const Feedback& feedback) const {
        if(feedback.routed.empty() || feedback.focus.empty())
            throw std::invalid_argument("empty timing feedback");
        for(auto id:feedback.focus) current_->positions.at(id);
        for(const auto& c:feedback.routed) {
            current_->positions.at(c.source); current_->positions.at(c.sink);
        }
    }
public:
    SearchState(Positions positions, std::vector<Net> nets, Feedback feedback):nets_(std::move(nets)) {
        current_=std::make_shared<const Version>(Version{std::move(positions),std::make_shared<const Feedback>(std::move(feedback))});
        validate(*current_->feedback);
        for(const auto& net:nets_) net_cost(net,current_->positions,current_->feedback->pressure);
    }
    SearchState(Positions positions, std::vector<Net> nets, Feedback feedback, PlacementConstraints constraints)
        :SearchState(std::move(positions),std::move(nets),std::move(feedback)) {
        constraints_=std::make_shared<const PlacementConstraints>(std::move(constraints));
        if(!constraints_->valid(current_->positions)) throw std::invalid_argument("illegal initial placement");
    }
    const Positions& positions() const { return current_->positions; }
    std::shared_ptr<const Feedback> feedback() const { return current_->feedback; }
    Cost cost(std::size_t id) {
        auto found=cache_.find(id);
        if(found!=cache_.end()) return found->second;
        auto value=net_cost(nets_.at(id),positions(),current_->feedback->pressure);
        cache_[id]=value; return value;
    }
    void begin(const Positions& changes) {
        if(saved_) throw std::logic_error("transaction already active");
        auto candidate=current_->positions;
        for(const auto& [id,p]:changes) candidate.at(id)=p;
        if(constraints_ && !constraints_->valid(candidate)) throw std::invalid_argument("illegal candidate placement");
        auto next=std::make_shared<const Version>(Version{std::move(candidate),current_->feedback});
        saved_=current_; install(std::move(next));
    }
    void replace_feedback(Feedback feedback) {
        validate(feedback);
        auto next=std::make_shared<const Version>(Version{positions(),std::make_shared<const Feedback>(std::move(feedback))});
        install(std::move(next));
    }
    void accept() {
        if(!saved_) throw std::logic_error("no active transaction");
        saved_.reset();
    }
    void reject() {
        if(!saved_) throw std::logic_error("no active transaction");
        auto prior=std::move(saved_); install(std::move(prior));
    }
};
}
