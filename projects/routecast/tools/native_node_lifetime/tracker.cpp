#include <cstddef>
#include <cstdlib>
static const void* tracked[100000]{};
long routecast_live_import_nodes=0;
static std::size_t highwater=0;
void routecast_track_import_node(const void* p){
 for(std::size_t i=0;i<100000;++i)if(!tracked[i]){tracked[i]=p;if(i>=highwater)highwater=i+1;++routecast_live_import_nodes;return;}
 std::abort();
}
static void untrack(void* p) noexcept {
 for(std::size_t i=0;i<highwater;++i)if(tracked[i]==p && p){tracked[i]=nullptr;--routecast_live_import_nodes;return;}
}
extern "C" void real_delete(void*) asm("__real__ZdlPv");
extern "C" void wrap_delete(void*) asm("__wrap__ZdlPv");
extern "C" void wrap_delete(void* p){untrack(p);real_delete(p);}
extern "C" void real_sized_delete(void*,std::size_t) asm("__real__ZdlPvm");
extern "C" void wrap_sized_delete(void*,std::size_t) asm("__wrap__ZdlPvm");
extern "C" void wrap_sized_delete(void* p,std::size_t n){untrack(p);real_sized_delete(p,n);}
