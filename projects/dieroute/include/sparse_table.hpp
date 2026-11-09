#pragma once
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <vector>
namespace dieroute {
// Epoch-tagged open addressing: storage follows the largest touched set, never
// the graph's ID range. References expire on insertion/reset. No hash iteration
// participates in search ordering. Small Epoch types allow wrap tests.
template<class Value, class Epoch = std::uint32_t> class SparseNodeTable {
    static_assert(std::is_unsigned<Epoch>::value, "unsigned epoch required");
    struct Bucket { std::uint32_t node=0, index=0; Epoch epoch=0; };
    std::vector<Bucket> buckets_;
    std::vector<Value> values_;
    Value absent_;
    Epoch epoch_=1;
    static std::uint64_t hash(std::uint32_t key) {
        std::uint64_t x=key; x=(x^(x>>16))*0x7feb352dU;
        x=(x^(x>>15))*0x846ca68bU; return x^(x>>16);
    }
    std::size_t slot(std::uint32_t node) const {
        auto pos=hash(node)&(buckets_.size()-1);
        while(buckets_[pos].epoch==epoch_ && buckets_[pos].node!=node)
            pos=(pos+1)&(buckets_.size()-1);
        return pos;
    }
    void grow() {
        const auto size=buckets_.empty()?16:buckets_.size()*2;
        if(size<buckets_.size())throw std::length_error("sparse table capacity overflow");
        std::vector<Bucket> next(size);
        for(const auto& b:buckets_)if(b.epoch==epoch_) {
            auto pos=hash(b.node)&(size-1);
            while(next[pos].epoch==epoch_)pos=(pos+1)&(size-1);
            next[pos]=b;
        }
        buckets_.swap(next);
    }
public:
    explicit SparseNodeTable(Value absent=Value{}):absent_(absent){}
    void reset() {
        values_.clear();
        if(epoch_==std::numeric_limits<Epoch>::max()) {
            for(auto& b:buckets_)b.epoch=0;
            epoch_=1;
        } else ++epoch_;
    }
    const Value& get(std::uint32_t node) const {
        if(buckets_.empty())return absent_;
        const auto& b=buckets_[slot(node)];
        return b.epoch==epoch_?values_[b.index]:absent_;
    }
    bool contains(std::uint32_t node) const {
        return !buckets_.empty() && buckets_[slot(node)].epoch==epoch_;
    }
    Value& touch(std::uint32_t node) {
        if(!buckets_.empty()) {
            auto& b=buckets_[slot(node)];
            if(b.epoch==epoch_)return values_[b.index];
        }
        if(values_.size()>=UINT32_MAX)throw std::length_error("sparse index overflow");
        if(buckets_.empty() || (values_.size()+1)>buckets_.size()/2)grow();
        const auto pos=slot(node), index=values_.size();
        values_.push_back(absent_);
        buckets_[pos]={node,static_cast<std::uint32_t>(index),epoch_};
        return values_.back();
    }
    std::size_t size() const {return values_.size();}
    std::size_t retained_bytes() const {return buckets_.capacity()*sizeof(Bucket)+values_.capacity()*sizeof(Value);}
};

}
