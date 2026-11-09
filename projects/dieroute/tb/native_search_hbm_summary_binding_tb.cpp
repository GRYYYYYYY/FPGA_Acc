#include "native_search_hbm_summary_binding.hpp"
#include "native_worker_shadows.hpp"
#include <cassert>
#include <cstring>
using namespace dieroute;
int main(){
 auto packet=NativeSummaryPacket::make(9,17,42,0,2,2,{5,7,11});auto bytes=packet.encode();packet=NativeSummaryPacket::decode(bytes.data());
 NativeSearchResourceObservation output{};
 auto bind=[&](const NativeSummaryPacket& p,unsigned owner=0,unsigned worker=2,unsigned membership=5,std::uint64_t session=9,std::uint64_t epoch=3,std::uint64_t serial=17){return native_search_bind_summary(p.words.data(),42,owner,worker,membership,serial,session,epoch,output);};
 assert(bind(packet)==NativeSummaryBindingStatus::ok);assert(output.node==42&&output.version==11&&output.occupancy==5&&output.history==7&&output.session==9&&output.epoch==3&&output.owner==0);
 auto retained=output;
 for(unsigned fault=0;fault<10;++fault){auto bad=packet;
  switch(fault){case 0:bad.words[0]=8;break;case 1:bad.words[1]^=1;break;case 2:bad.words[1]^=1ull<<32;break;case 3:bad.words[1]^=1ull<<40;break;case 4:bad.words[1]^=3ull<<48;break;case 5:bad.words[1]|=1ull<<56;break;case 6:bad.words[5]=18;break;case 7:bad.words[6]=1;break;case 8:bad.words[7]=1;break;case 9:bad.words[3]=UINT64_MAX;break;}
  assert(bind(bad)==NativeSummaryBindingStatus::invalid);assert(std::memcmp(&retained,&output,sizeof(output))==0);
 }
 assert(bind(packet,0,2,4)==NativeSummaryBindingStatus::invalid);
 assert(bind(packet,1,2,6)==NativeSummaryBindingStatus::invalid);
 assert(bind(packet,0,0,5)==NativeSummaryBindingStatus::invalid);
 assert(bind(packet,0,2,5,9,0)==NativeSummaryBindingStatus::invalid);
 packet.words[1]^=1ull<<48;assert(bind(packet)==NativeSummaryBindingStatus::ok);
 NativeSearchResourceObservation journal[4]{};std::uint32_t used=0;std::uint64_t cost=123;
 auto observe=[&](std::uint64_t serial){return native_search_observe_summary<4>(packet.words.data(),42,0,2,5,serial,9,3,journal,4,used,false,3,cost);};
 assert(observe(17)==NativeSearchObservationStatus::ok&&used==1&&cost==23&&journal[0].version==11);
 assert(observe(18)==NativeSearchObservationStatus::invalid&&used==1&&cost==23);
 packet.words[3]=UINT64_MAX-1;assert(observe(17)==NativeSearchObservationStatus::cost_overflow&&used==2&&cost==23&&journal[1].history==UINT64_MAX-1);
}
