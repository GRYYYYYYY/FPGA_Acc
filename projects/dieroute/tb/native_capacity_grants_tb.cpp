#include "native_capacity_grants.hpp"
#include <stdexcept>
#include <iostream>
using namespace dieroute;
void check(bool ok){if(!ok)throw std::runtime_error("native capacity grant invariant");}
int main(){
 std::map<std::uint32_t,NativeGrantObservation> authority{{10,{3,1,{}}},{20,{4,1,{7}}},{30,{5,2,{}}}};
 auto observe=[&](auto node){return authority.at(node);};NativeCapacityGrants grants;
 auto denied=grants.acquire(8,{10,20},observe);check(denied.status==NativeGrantStatus::capacity&&grants.active()==0);
 auto a=grants.acquire(8,{10},observe);check(a.status==NativeGrantStatus::granted);
 auto b=grants.acquire(8,{10},observe);check(b.status==NativeGrantStatus::granted&&b.handle!=a.handle);
 check(grants.acquire(9,{10},observe).status==NativeGrantStatus::capacity);
 check(grants.release(a.handle,9)==NativeGrantStatus::missing&&grants.active()==2);
 check(grants.release(a.handle,8)==NativeGrantStatus::released);
 check(grants.acquire(9,{10},observe).status==NativeGrantStatus::capacity);
 check(grants.validate(b.handle,8,observe)==NativeGrantStatus::valid);
 ++authority[10].version;check(grants.validate(b.handle,8,observe)==NativeGrantStatus::stale);
 check(grants.release(b.handle,8)==NativeGrantStatus::released);
 auto c=grants.acquire(9,{10},observe);check(c.status==NativeGrantStatus::granted);
 check(grants.release(a.handle,8)==NativeGrantStatus::missing&&grants.active()==1);
 check(grants.acquire(7,{20},observe).status==NativeGrantStatus::granted);
 check(grants.acquire(1,{30},observe).status==NativeGrantStatus::granted);
 check(grants.acquire(2,{30},observe).status==NativeGrantStatus::granted);
 check(grants.acquire(3,{30},observe).status==NativeGrantStatus::capacity);
 auto before=grants.active();check(grants.acquire(8,{30,10},observe).status==NativeGrantStatus::invalid&&grants.active()==before);
 auto snapshot=authority;try{grants.acquire(8,{40},observe);check(false);}catch(const std::out_of_range&){}check(grants.active()==before);
 check(authority[10].nets.empty()&&authority[20].nets==std::set<std::uint32_t>{7});
 std::cout<<"native grant sharing, atomic rejection, stale-version and handle checks passed\n";
}
