#include "placement.hpp"
#include <iostream>
using namespace tileplace_snapshot;
void require(bool v) {if(!v) throw std::runtime_error("placement invariant failed");}
int main() {
    Point a{0,0,0,0},b{0,0,1,0},c{0,0,0,1};
    std::map<Point,std::string> sites{{a,"clb"},{b,"clb"},{c,"clb"},{{-1,0,0,0},"clb"},{{9,0,0,0},"dsp"}};
    std::map<std::uint32_t,Block> blocks{{0,{"clb",std::nullopt,{}}},{1,{"clb",std::nullopt,{}}}};
    std::map<Point,std::uint32_t> occupied{{a,0},{b,1}};
    require(valid_trial({{0,b},{1,a}},{0,1},occupied,blocks,sites));
    require(!valid_trial({{0,b}},{0},occupied,blocks,sites));
    require(!valid_trial({{0,a},{1,a}},{0,1},occupied,blocks,sites));
    blocks[0].fixed[2]=0;
    require(!valid_trial({{0,b}},{0,1},occupied,blocks,sites));
    blocks[0].fixed[2].reset();
    blocks[0].regions=std::vector<Region>{{0,0,0,0,1,1,-1}};
    require(valid_trial({{0,c}},{0},occupied,blocks,sites));
    require(!valid_trial({{0,a}},{0},occupied,blocks,sites));
    require(page_coordinate(-1,4)==-1 && page_coordinate(-4,4)==-1 && page_coordinate(-5,4)==-2);
    auto roots=candidate_roots(a,"clb",sites,4,4,8);
    require(roots.size()==3 && roots[0]==a && roots[1]==b && roots[2]==Point{-1,0,0,0});
    auto moved=translated({0,1},{4,5,2,3},{{0,a},{1,b}});
    require(moved.at(0)==Point{4,5,2,3} && moved.at(1)==Point{4,5,3,3});
    std::cout<<"four-dimensional sites, occupancy, regions, fixed constraints and macro translation passed\n";
}
