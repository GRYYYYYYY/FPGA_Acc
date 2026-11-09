#include "native_search_hbm_observation.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_observation_hbm(const std::uint64_t*,NativeSearchResourceObservation*,std::uint64_t*,std::uint32_t,std::uint64_t,std::uint64_t,std::uint64_t,std::uint32_t,std::uint64_t);
int main(){
 std::array<NativeSearchResourceObservation,1024> journal{};std::uint32_t count=0;std::uint64_t cost=777;
 NativeSearchResourceObservation value{42,3,2,4,9,1,2,0};
 auto invoke=[&](bool own){alignas(64) std::uint64_t metadata[8]={count,99,cost};alignas(64) std::uint64_t words[8];std::memcpy(words,&value,sizeof(value));dieroute_native_search_observation_hbm(words,journal.data(),metadata,3,42,9,1,own?1:0,10);count=metadata[0];cost=metadata[2];return NativeSearchObservationStatus(metadata[1]);};
 assert(invoke(true)==NativeSearchObservationStatus::ok&&count==1&&cost==15);
 value.version=4;assert(invoke(false)==NativeSearchObservationStatus::ok&&count==2&&cost==25);assert(journal[0].version==3&&journal[1].version==4);
 value.history=UINT64_MAX;cost=123;assert(invoke(false)==NativeSearchObservationStatus::cost_overflow&&count==3&&cost==123);assert(journal[2].history==UINT64_MAX);
 auto before=journal;assert(invoke(false)==NativeSearchObservationStatus::journal_full);assert(count==3&&cost==123&&std::memcmp(before.data(),journal.data(),sizeof(journal))==0);
 value.epoch=2;assert(invoke(false)==NativeSearchObservationStatus::invalid);assert(count==3&&std::memcmp(before.data(),journal.data(),sizeof(journal))==0);
}
