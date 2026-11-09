#pragma once
#include "score.hpp"
#include <string>

namespace tileplace_snapshot {
using Unit=std::vector<std::uint32_t>;
struct Proposal {
    std::string kind;
    std::vector<Unit> units;
    Positions trial;
    std::set<std::uint32_t> touched_nets;
    std::set<Point> write_sites;
    std::int64_t score;
    auto identity() const {return std::tie(kind,units,trial);}
};
template<class T> bool intersects(const std::set<T>& a,const std::set<T>& b) {
    for(const auto& value:a) if(b.count(value)) return true;
    return false;
}
inline std::vector<Proposal> select_transactions(std::vector<Proposal> proposals) {
    for(auto& p:proposals) std::sort(p.units.begin(),p.units.end());
    std::sort(proposals.begin(),proposals.end(),[](const Proposal& a,const Proposal& b) {
        if(a.score!=b.score) return a.score<b.score;
        return a.identity()<b.identity();
    });
    std::set<Point> sites;
    std::set<std::uint32_t> nets;
    std::set<Unit> units;
    std::vector<Proposal> accepted;
    for(auto& p:proposals) {
        if(p.score>=0 || intersects(p.write_sites,sites) || intersects(p.touched_nets,nets)) continue;
        if(std::any_of(p.units.begin(),p.units.end(),[&](const Unit& u){return units.count(u);})) continue;
        sites.insert(p.write_sites.begin(),p.write_sites.end());
        nets.insert(p.touched_nets.begin(),p.touched_nets.end());
        units.insert(p.units.begin(),p.units.end());
        accepted.push_back(std::move(p));
    }
    return accepted;
}
}
