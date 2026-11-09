#include "transactions.hpp"
#include <iostream>
using namespace tileplace_snapshot;
int main() {
    std::vector<Proposal> proposals{
        {"move",{{0}},{{0,{1,0}}},{0},{{0,0},{1,0}},-2},
        {"move",{{1}},{{1,{2,0}}},{0},{{2,0},{3,0}},-1},
        {"move",{{2}},{{2,{4,0}}},{2},{{1,0},{4,0}},-1},
        {"move",{{0}},{{0,{5,0}}},{3},{{5,0},{6,0}},-1},
        {"move",{{4}},{{4,{7,0}}},{4},{{7,0},{8,0}},-1}};
    auto selected=select_transactions(proposals);
    if(selected.size()!=2 || selected[0].units[0][0]!=0 || selected[1].units[0][0]!=4)
        throw std::runtime_error("site/net/unit conflict selection differs");
    if(normalized_delta(3,2)!=-349526) throw std::runtime_error("negative rounding differs");
    std::cout<<"score ordering and site/net/unit conflict checks passed\n";
}
