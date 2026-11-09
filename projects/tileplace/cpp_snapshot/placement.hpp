#pragma once
#include "net_cost.hpp"
#include <optional>
#include <string>

namespace tileplace_snapshot {
struct Region {
    std::int32_t xmin,ymin,xmax,ymax,layer_low,layer_high,subtile=-1;
    bool contains(Point p) const {
        return xmin<=p.x && p.x<=xmax && ymin<=p.y && p.y<=ymax &&
               layer_low<=p.layer && p.layer<=layer_high && (subtile==-1 || subtile==p.subtile);
    }
};
struct Block {
    std::string type;
    std::optional<std::vector<Region>> regions;
    std::array<std::optional<std::int32_t>,4> fixed{};
};
inline bool valid_trial(const Positions& trial, const std::set<std::uint32_t>& changed,
    const std::map<Point,std::uint32_t>& occupied, const std::map<std::uint32_t,Block>& blocks,
    const std::map<Point,std::string>& sites) {
    std::set<Point> targets;
    for(const auto& [id,p]:trial) {
        if(!targets.insert(p).second) return false;
        const auto& block=blocks.at(id);
        auto site=sites.find(p);
        if(site==sites.end() || site->second!=block.type) return false;
        auto occupant=occupied.find(p);
        if(occupant!=occupied.end() && !changed.count(occupant->second)) return false;
        if(block.regions && !std::any_of(block.regions->begin(),block.regions->end(),
                                        [p](const Region& r){return r.contains(p);})) return false;
        std::array<std::int32_t,4> coordinates{p.x,p.y,p.subtile,p.layer};
        for(unsigned i=0;i<4;++i) if(block.fixed[i] && *block.fixed[i]!=coordinates[i]) return false;
    }
    return true;
}
inline std::int32_t page_coordinate(std::int32_t value,std::int32_t size) {
    if(size<=0) throw std::invalid_argument("nonpositive page size");
    auto result=value/size;
    return value%size<0 ? result-1:result;
}
inline std::vector<Point> candidate_roots(Point source,const std::string& type,
    const std::map<Point,std::string>& sites,std::int32_t width,std::int32_t height,std::size_t limit) {
    auto px=page_coordinate(source.x,width), py=page_coordinate(source.y,height);
    std::vector<Point> out;
    for(const auto& [p,t]:sites) {
        auto dx=std::int64_t(page_coordinate(p.x,width))-px;
        auto dy=std::int64_t(page_coordinate(p.y,height))-py;
        if(t==type && p.layer==source.layer && dx>=-1 && dx<=1 && dy>=-1 && dy<=1) out.push_back(p);
    }
    std::sort(out.begin(),out.end(),[source](Point a,Point b) {
        return std::make_tuple(distance(a,source),a.layer,a.y,a.x,a.subtile)<
               std::make_tuple(distance(b,source),b.layer,b.y,b.x,b.subtile);
    });
    if(out.size()>limit) out.resize(limit);
    return out;
}
inline Positions translated(const std::vector<std::uint32_t>& unit,Point target,const Positions& positions) {
    if(unit.empty()) throw std::invalid_argument("empty placement unit");
    auto root=positions.at(unit.front());
    Positions result;
    for(auto id:unit) {
        auto p=positions.at(id);
        auto shift=[](std::int32_t v,std::int32_t t,std::int32_t r) {
            auto q=std::int64_t(v)+t-r;
            if(q<INT32_MIN || q>INT32_MAX) throw std::overflow_error("translated coordinate overflow");
            return std::int32_t(q);
        };
        result[id]={shift(p.x,target.x,root.x),shift(p.y,target.y,root.y),
                    shift(p.subtile,target.subtile,root.subtile),shift(p.layer,target.layer,root.layer)};
    }
    return result;
}
struct PlacementConstraints {
    std::map<std::uint32_t,Block> blocks;
    std::map<Point,std::string> sites;
    std::vector<std::vector<std::uint32_t>> macros;
    Positions reference;
    bool valid(const Positions& positions) const {
        if(positions.size()!=blocks.size()) return false;
        std::set<std::uint32_t> all;
        for(const auto& [id,block]:blocks) { (void)block; if(!positions.count(id)) return false; all.insert(id); }
        if(!valid_trial(positions,all,{},blocks,sites)) return false;
        std::set<std::uint32_t> macro_members;
        for(const auto& unit:macros) {
            if(unit.empty()) return false;
            for(auto id:unit) if(!macro_members.insert(id).second || !positions.count(id) || !reference.count(id)) return false;
            auto shifted=translated(unit,positions.at(unit.front()),reference);
            for(auto id:unit) if(!(shifted.at(id)==positions.at(id))) return false;
        }
        return true;
    }
};
}
