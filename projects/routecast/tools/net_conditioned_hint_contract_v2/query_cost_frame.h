#pragma once
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <exception>
#include <limits>
#include <mutex>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>
#include <type_traits>

namespace routecast_v2 {
struct FrameError : std::runtime_error { using std::runtime_error::runtime_error; };
inline uint32_t cost_bits(float value) { uint32_t b; std::memcpy(&b,&value,4); return b; }
inline void set_cost_bits(float& value,uint32_t b) { std::memcpy(&value,&b,4); }

// Accessor contract: size(), identity() and word(index) are noexcept;
// word returns only a float& to the accumulated-cost field. Queries are serial.
struct FrameClaim { uint32_t node,net,hint_bits; };
struct FrameToken { uint64_t owner,generation,epoch; uint32_t net; };
inline std::set<const void*>& borrowed_stores() {static std::set<const void*> r;return r;}
inline std::mutex& borrowed_mutex() {static std::mutex m;return m;}
inline uint64_t allocate_owner() {
    static std::atomic<uint64_t> next{1};auto value=next.load();
    do {if(value==std::numeric_limits<uint64_t>::max())throw FrameError("owner identity exhausted");}
    while(!next.compare_exchange_weak(value,value+1));return value;
}
class VectorCostView {
public:
    explicit VectorCostView(std::vector<float>& values):values_(&values) {}
    size_t size() const noexcept {return values_->size();}
    const void* identity() const noexcept {return values_;}
    float& word(size_t n) const noexcept {return (*values_)[n];}
    void rebind(std::vector<float>& values) noexcept {values_=&values;}
private: std::vector<float>* values_;
};
template<class Store>
class QueryCostFrame {
    static_assert(std::is_same<decltype(std::declval<Store&>().word(size_t{})),float&>::value,"cost accessor must return float&");
    static_assert(noexcept(std::declval<Store&>().word(size_t{})) && noexcept(std::declval<const Store&>().size()) && noexcept(std::declval<const Store&>().identity()),"accessors must be noexcept");
public:
    using Claim=FrameClaim;
    using Token=FrameToken;
    class Scope;
    QueryCostFrame(Store& costs,uint32_t net_count,uint64_t epoch,
                   const std::vector<Claim>& claims,bool cold=true,uint32_t workers=1)
        :costs_(costs),size_(costs.size()),identity_(costs.identity()),epoch_(epoch),cold_(cold),workers_(workers),owned_(net_count) {
        if(!identity_ || !net_count || !epoch || size_>std::numeric_limits<uint32_t>::max())throw FrameError("context domain");
        uint32_t previous=0;bool first=true;
        for(const auto& c:claims) {
            float value;std::memcpy(&value,&c.hint_bits,4);
            if(c.node>=size_ || c.net>=net_count || (!first && c.node<=previous) || !std::isfinite(value) || value<1.f)
                throw FrameError("claim domain/order/value");
            first=false;previous=c.node;owned_[c.net].push_back(c);has_claims_=true;
        }
        owner_=allocate_owner();
        std::lock_guard<std::mutex> lock(borrowed_mutex());
        if(!borrowed_stores().insert(identity_).second)throw FrameError("cost store already borrowed");
    }
    QueryCostFrame(const QueryCostFrame&)=delete;
    QueryCostFrame& operator=(const QueryCostFrame&)=delete;
    QueryCostFrame(QueryCostFrame&&)=delete;
    QueryCostFrame& operator=(QueryCostFrame&&)=delete;
    ~QueryCostFrame() noexcept {
        if(active_)std::terminate(); // Never silently leak a cost exemption into subsequent queries.
        std::lock_guard<std::mutex> lock(borrowed_mutex());
        if(borrowed_stores().erase(identity_)!=1)std::terminate();
    }
    Token begin(uint64_t epoch,uint32_t net,uint32_t iteration,bool enabled=true) {
        if(active_)throw FrameError("nested query frame");
        if(epoch!=epoch_ || net>=owned_.size() || !iteration || (costs_.identity()!=identity_ || costs_.size()!=size_))throw FrameError("stale/invalid query context");
        const bool apply=enabled && iteration==1;
        if(apply && has_claims_ && (!cold_ || workers_!=1))throw FrameError("hint requires cold serial routing");
        if(generation_==std::numeric_limits<uint64_t>::max())throw FrameError("generation exhausted");
        std::vector<std::pair<uint32_t,uint32_t>> backup;
        if(apply) {
            backup.reserve(owned_[net].size());
            for(const auto& c:owned_[net]) {
                const auto bits=cost_bits(costs_.word(c.node));
                if(bits!=c.hint_bits)throw FrameError("unexpected history before exemption");
                backup.emplace_back(c.node,bits);
            }
        }
        // All validation/allocation completes before any external cost word changes.
        backup_=std::move(backup);token_={owner_,++generation_,epoch_,net};active_=true;
        for(const auto& entry:backup_)set_cost_bits(costs_.word(entry.first),one_bits);
        return token_;
    }
    void finish(Token token) {
        if(!active_ || token.owner!=token_.owner || token.generation!=token_.generation ||
           token.epoch!=token_.epoch || token.net!=token_.net || (costs_.identity()!=identity_ || costs_.size()!=size_))
            throw FrameError("foreign/stale query token or cost domain");
        // Validate the entire write set before restoring anything. Preserve unexpected history.
        for(const auto& entry:backup_)
            if(cost_bits(costs_.word(entry.first))!=one_bits)throw FrameError("unexpected history during exemption");
        for(const auto& entry:backup_)set_cost_bits(costs_.word(entry.first),entry.second);
        backup_.clear();active_=false;
    }
    bool active() const noexcept { return active_; }
    const std::vector<Claim>& claims_for(uint32_t net) const { return owned_.at(net); }
    Scope scoped(uint64_t epoch,uint32_t net,uint32_t iteration,bool enabled=true);
    static constexpr uint32_t one_bits=0x3f800000;
private:
    Store& costs_;size_t size_;const void* identity_;uint64_t epoch_,owner_=0,generation_=0;
    bool cold_,has_claims_=false,active_=false;uint32_t workers_;Token token_{};
    std::vector<std::vector<Claim>> owned_;
    std::vector<std::pair<uint32_t,uint32_t>> backup_;
};
template<class Store>
class QueryCostFrame<Store>::Scope {
public:
    Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
    Scope(Scope&&)=delete;Scope& operator=(Scope&&)=delete;
    ~Scope() noexcept { if(open_) { try { frame_.finish(token_); } catch(...) { std::terminate(); } } }
    void close() { frame_.finish(token_);open_=false; }
private:
    friend class QueryCostFrame<Store>;
    Scope(QueryCostFrame<Store>& frame,uint64_t epoch,uint32_t net,uint32_t iteration,bool enabled)
        :frame_(frame),token_(frame.begin(epoch,net,iteration,enabled)) {}
    QueryCostFrame<Store>& frame_;FrameToken token_;bool open_=true;
};
template<class Store>
inline typename QueryCostFrame<Store>::Scope QueryCostFrame<Store>::scoped(uint64_t epoch,uint32_t net,uint32_t iteration,bool enabled) {
    return Scope(*this,epoch,net,iteration,enabled);
}
} // namespace routecast_v2
