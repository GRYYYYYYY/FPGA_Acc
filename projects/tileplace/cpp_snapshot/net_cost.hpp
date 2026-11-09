#pragma once
#include "pressure_snapshot.hpp"
#include <array>
#include <set>

namespace tileplace_snapshot {
using Positions = std::map<std::uint32_t, Point>;
struct Connection { std::uint32_t source, sink; std::uint64_t weight; };
struct Net { std::vector<std::uint32_t> members; std::vector<Connection> connections; };
using Cost = std::array<std::uint64_t, 4>; // HPWL, criticality, routed timing, congestion
inline std::uint64_t checked_add(std::uint64_t a, std::uint64_t b) {
    if (b > std::numeric_limits<std::uint64_t>::max()-a) throw std::overflow_error("cost sum overflow");
    return a+b;
}
inline std::uint64_t checked_product(std::uint64_t a, std::uint64_t b) {
    if (a && b > std::numeric_limits<std::uint64_t>::max()/a) throw std::overflow_error("cost product overflow");
    return a*b;
}
inline std::uint64_t distance(Point a, Point b) {
    auto dx=std::int64_t(a.x)-b.x, dy=std::int64_t(a.y)-b.y;
    return std::uint64_t(dx<0?-dx:dx)+std::uint64_t(dy<0?-dy:dy);
}
inline Cost net_cost(const Net& net, const Positions& positions, const PressureSnapshot& pressure) {
    Cost out{};
    if (!net.members.empty()) {
        auto p=positions.at(net.members.front());
        auto xmin=p.x,xmax=p.x,ymin=p.y,ymax=p.y;
        for (auto id:net.members) {
            p=positions.at(id); xmin=std::min(xmin,p.x); xmax=std::max(xmax,p.x);
            ymin=std::min(ymin,p.y); ymax=std::max(ymax,p.y);
        }
        out[0]=distance({xmin,ymin},{xmax,ymax});
    }
    for (const auto& c:net.connections) {
        auto a=positions.at(c.source), b=positions.at(c.sink);
        out[1]=checked_add(out[1],checked_product(c.weight,distance(a,b)));
        out[3]=checked_add(out[3],pressure.connection(a,b));
    }
    return out;
}
inline std::pair<Cost,Cost> cost_pair(const std::vector<Net>& touched,
    const std::set<std::uint32_t>& changed, const Positions& before, const Positions& after,
    const std::vector<Connection>& routed, const PressureSnapshot& pressure) {
    // Reject incomplete change sets: otherwise incremental Python semantics differ.
    if (before.size()!=after.size()) throw std::invalid_argument("placement block set differs");
    for (const auto& [id,p]:before) {
        auto q=after.at(id);
        if (!(p==q) && !changed.count(id))
            throw std::invalid_argument("unreported changed block");
    }
    Cost a{},b{};
    for (const auto& net:touched) {
        auto x=net_cost(net,before,pressure), y=net_cost(net,after,pressure);
        for (unsigned i=0;i<4;++i) { a[i]=checked_add(a[i],x[i]); b[i]=checked_add(b[i],y[i]); }
    }
    for (const auto& c:routed) if (changed.count(c.source)||changed.count(c.sink)) {
        a[2]=checked_add(a[2],checked_product(c.weight,distance(before.at(c.source),before.at(c.sink))));
        b[2]=checked_add(b[2],checked_product(c.weight,distance(after.at(c.source),after.at(c.sink))));
    }
    return {a,b};
}
}
