#pragma once
#include "prince_live_view_v2.h"
namespace routecast_live {
class ReadyGate {
 Identity identity_;bool initialized_=false,emitted_=false;int last_=0,streak_=0;
public:
 bool observe(const View& view,uint64_t nodes,uint64_t overused){
  auto stamp=view.identity();auto profile=stamp;profile.iteration=0;if(!initialized_){identity_=profile;initialized_=true;}
  if(!(profile==identity_)||stamp.iteration!=last_+1||nodes==0||overused>nodes)throw std::logic_error("ready_gate_identity_or_sequence");last_=stamp.iteration;streak_=(last_>=2&&overused<=nodes/100)?streak_+1:0;
  if(streak_>=2&&!emitted_){emitted_=true;return true;}return false;
 }
 int streak()const{return streak_;}
};
}
