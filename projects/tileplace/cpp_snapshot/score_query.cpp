#include "score.hpp"
#include <iostream>
int main() {
    unsigned count; std::cin>>count;
    while(count--) {
        tileplace_snapshot::Cost before,after;
        std::array<std::int32_t,3> weights;
        for(auto& value:before) std::cin>>value;
        for(auto& value:after) std::cin>>value;
        for(auto& value:weights) std::cin>>value;
        std::cout<<tileplace_snapshot::transaction_score(before,after,weights)<<'\n';
    }
}
