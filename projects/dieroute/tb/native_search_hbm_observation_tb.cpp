#include "native_search_hbm_observation.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 std::array<NativeSearchResourceObservation,3> journal{};std::uint32_t count=0;std::uint64_t cost=777;
 NativeSearchResourceObservation value{42,3,2,4,9,1,2,0};
 assert(native_search_observe_cost<3>(value,42,9,1,journal.data(),3,count,true,10,cost)==NativeSearchObservationStatus::ok&&count==1&&cost==15);
 value.version=4;assert(native_search_observe_cost<3>(value,42,9,1,journal.data(),3,count,false,10,cost)==NativeSearchObservationStatus::ok&&count==2&&cost==25);assert(journal[0].version==3&&journal[1].version==4);
 value.history=UINT64_MAX;cost=123;assert(native_search_observe_cost<3>(value,42,9,1,journal.data(),3,count,false,10,cost)==NativeSearchObservationStatus::cost_overflow&&count==3&&cost==123);assert(journal[2].history==UINT64_MAX);
 auto before=journal;assert(native_search_observe_cost<3>(value,42,9,1,journal.data(),3,count,false,10,cost)==NativeSearchObservationStatus::journal_full);assert(count==3&&cost==123&&std::memcmp(before.data(),journal.data(),sizeof(journal))==0);
 value.epoch=2;assert(native_search_observe_cost<3>(value,42,9,1,journal.data(),3,count,false,10,cost)==NativeSearchObservationStatus::invalid);assert(count==3&&std::memcmp(before.data(),journal.data(),sizeof(journal))==0);
}
