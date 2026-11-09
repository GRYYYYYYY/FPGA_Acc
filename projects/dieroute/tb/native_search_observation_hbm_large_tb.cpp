#include "native_search_hbm_observation.hpp"
#include <array>
#include <cassert>
#include <cstring>
using namespace dieroute;
extern "C" void dieroute_native_search_observation_hbm(const std::uint64_t*,NativeSearchResourceObservation*,std::uint64_t*,std::uint32_t,std::uint64_t,std::uint64_t,std::uint64_t,std::uint32_t,std::uint64_t);
int main(){
 std::array<NativeSearchResourceObservation,1024> journal{},golden{};
 alignas(64) std::uint64_t metadata[8]={0,99,777,11,12,13,14,15};
 auto invoke=[&](NativeSearchResourceObservation value,std::uint32_t own,std::uint64_t present,std::uint32_t capacity,std::uint64_t expected_node,NativeSearchObservationStatus expected){
  alignas(64) std::uint64_t words[8];std::memcpy(words,&value,sizeof(value));
  auto before_words=std::array<std::uint64_t,8>{};std::memcpy(before_words.data(),words,sizeof(words));
  dieroute_native_search_observation_hbm(words,journal.data(),metadata,capacity,expected_node,9,1,own,present);
  assert(metadata[1]==std::uint64_t(expected));
  assert(std::memcmp(words,before_words.data(),sizeof(words))==0);
  for(unsigned i=3;i<8;++i)assert(metadata[i]==8+i);
  assert(std::memcmp(journal.data(),golden.data(),sizeof(journal))==0);
 };
 for(unsigned i=0;i<1024;++i){
  // Repeated nodes with changing versions must retain every individual read.
  NativeSearchResourceObservation value{i%17,i+1,i%31,i%101,9,1,i%8,0};
  bool own=i%2;std::uint64_t present=i%13;
  std::uint64_t expected_cost=1+value.history+present*(value.occupancy-(own&&value.occupancy?1:0));
  golden[i]=value;
  invoke(value,own,present,1024,value.node,NativeSearchObservationStatus::ok);
  assert(metadata[0]==i+1&&metadata[2]==expected_cost);
 }
 auto retained_cost=metadata[2];
 NativeSearchResourceObservation value{42,1025,2,4,9,1,2,0};
 invoke(value,0,10,1024,42,NativeSearchObservationStatus::journal_full);
 assert(metadata[0]==1024&&metadata[2]==retained_cost);
 // Explicit coordinator reset; old journal tail remains untouched.
 metadata[0]=0;metadata[2]=123;
 value.history=UINT64_MAX;golden[0]=value;
 invoke(value,0,10,1024,42,NativeSearchObservationStatus::cost_overflow);
 assert(metadata[0]==1&&metadata[2]==123);
 value.history=4;
 for(unsigned kind=0;kind<7;++kind){
  auto bad=value;unsigned own=0,capacity=1024;std::uint64_t node=42;
  if(kind==0)bad.owner=8;
  if(kind==1)bad.reserved=1;
  if(kind==2)bad.session=10;
  if(kind==3)bad.epoch=2;
  if(kind==4)node=43;
  if(kind==5)own=2;
  if(kind==6)capacity=1025;
  invoke(bad,own,10,capacity,node,NativeSearchObservationStatus::invalid);
  assert(metadata[0]==1&&metadata[2]==123);
 }
}
