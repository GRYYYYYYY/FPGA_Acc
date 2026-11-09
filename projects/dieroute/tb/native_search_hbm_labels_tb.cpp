#include "native_search_hbm_labels.hpp"
#include <array>
#include <cassert>
#include <map>
using namespace dieroute;
int main(){
 std::array<NativeSearchLabelSlot,7> slots{};std::map<unsigned,unsigned> assigned;
 for(unsigned i=0;i<7;++i){unsigned node=i*7;auto r=native_search_label_lookup<7>(slots.data(),7,1,node);assert(r.status==NativeLabelLookup::missing);slots[r.slot]={1,100+i,1,node,i,0,0,0};assigned[node]=r.slot;}
 for(auto x:assigned){auto r=native_search_label_lookup<7>(slots.data(),7,1,x.first);assert(r.status==NativeLabelLookup::found&&r.slot==x.second&&slots[r.slot].node==x.first);}
 auto r=native_search_label_lookup<7>(slots.data(),7,1,49);assert(r.status==NativeLabelLookup::full);
 for(unsigned i=0;i<7;++i){r=native_search_label_lookup<7>(slots.data(),7,2,i*7);assert(r.status==NativeLabelLookup::missing);slots[r.slot]={2,200+i,1,i*7,i,0,0,0};}
 for(unsigned i=0;i<7;++i){r=native_search_label_lookup<7>(slots.data(),7,2,i*7);assert(r.status==NativeLabelLookup::found&&slots[r.slot].cost==200+i);}
 assert(native_search_label_lookup<7>(slots.data(),7,1,0).status==NativeLabelLookup::invalid);
 assert(native_search_label_lookup<7>(slots.data(),0,2,0).status==NativeLabelLookup::invalid);
 assert(native_search_label_lookup<7>(slots.data(),8,2,0).status==NativeLabelLookup::invalid);
 assert(native_search_label_lookup<7>(slots.data(),7,0,0).status==NativeLabelLookup::invalid);
 assert(native_search_label_lookup<7>(slots.data(),7,2,UINT32_MAX).status==NativeLabelLookup::invalid);
}
