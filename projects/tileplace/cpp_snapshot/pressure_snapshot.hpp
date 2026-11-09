#pragma once
#include <algorithm>
#include <cstdint>
#include <limits>
#include <map>
#include <stdexcept>
#include <tuple>
#include <vector>

namespace tileplace_snapshot {
struct Edge { std::int32_t x0, y0, x1, y1; std::uint64_t weight; };
struct Point {
    std::int32_t x, y, subtile=0, layer=0;
    auto key() const { return std::tie(x,y,subtile,layer); }
    bool operator<(const Point& other) const { return key()<other.key(); }
    bool operator==(const Point& other) const { return key()==other.key(); }
};

// Construct once, then share through shared_ptr<const PressureSnapshot>.
// Coordinates are sparse; queries never mutate feedback or its indexes.
class PressureSnapshot {
    struct Line {
        std::vector<std::int32_t> coordinates;
        std::vector<std::uint64_t> sums{0};
    };
    std::map<std::int32_t, Line> horizontal_, vertical_;
    static std::uint64_t add(std::uint64_t a, std::uint64_t b) {
        if (b > std::numeric_limits<std::uint64_t>::max() - a)
            throw std::overflow_error("pressure exceeds uint64");
        return a + b;
    }
    static std::uint64_t segment(const std::map<std::int32_t, Line>& lines,
                                 std::int32_t line, std::int32_t a, std::int32_t b) {
        auto found = lines.find(line);
        if (found == lines.end()) return 0;
        const auto& value = found->second;
        auto low = std::lower_bound(value.coordinates.begin(), value.coordinates.end(), std::min(a,b));
        auto high = std::lower_bound(value.coordinates.begin(), value.coordinates.end(), std::max(a,b));
        return value.sums[high-value.coordinates.begin()] - value.sums[low-value.coordinates.begin()];
    }
public:
    explicit PressureSnapshot(std::vector<Edge> edges) {
        std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) {
            return std::tie(a.x0,a.y0,a.x1,a.y1) < std::tie(b.x0,b.y0,b.x1,b.y1);
        });
        std::map<std::int32_t, std::map<std::int32_t,std::uint64_t>> h, v;
        for (std::size_t i=0; i<edges.size(); ++i) {
            const auto& e=edges[i];
            if (i && std::tie(e.x0,e.y0,e.x1,e.y1)==std::tie(edges[i-1].x0,edges[i-1].y0,edges[i-1].x1,edges[i-1].y1))
                throw std::invalid_argument("duplicate pressure edge");
            if (e.y0==e.y1 && std::int64_t(e.x1)==std::int64_t(e.x0)+1) h[e.y0][e.x0]=e.weight;
            else if (e.x0==e.x1 && std::int64_t(e.y1)==std::int64_t(e.y0)+1) v[e.x0][e.y0]=e.weight;
        }
        auto build=[](const auto& input, auto& output) {
            for (const auto& [key, entries]: input) {
                auto& line=output[key];
                for (const auto& [coordinate, weight]: entries) {
                    line.coordinates.push_back(coordinate);
                    line.sums.push_back(add(line.sums.back(),weight));
                }
            }
        };
        build(h,horizontal_); build(v,vertical_);
    }
    std::uint64_t path(Point a, Point b, bool horizontal_first) const {
        auto distance=[](std::int32_t x,std::int32_t y) {
            auto d=std::int64_t(x)-std::int64_t(y);
            return std::uint64_t(d<0 ? -d : d);
        };
        auto base=(distance(a.x,b.x)+distance(a.y,b.y))*65536ULL;
        return add(add(base,segment(horizontal_,horizontal_first?a.y:b.y,a.x,b.x)),
                   segment(vertical_,horizontal_first?b.x:a.x,a.y,b.y));
    }
    std::uint64_t connection(Point a, Point b) const {
        return std::min(path(a,b,true),path(a,b,false));
    }
};
}
