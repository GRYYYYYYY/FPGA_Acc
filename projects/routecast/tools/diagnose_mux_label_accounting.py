"""Observe frozen mux32 failure without changing search decisions or limit."""
import ctypes,json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from native_capacity_rc_search import NativeCapacityRC
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_label_accounting_2026-10-06';out.mkdir()
original=ROOT/'build/rc_capacity_native_2026-10-06/search.cpp'
text=original.read_text().replace('#include <cstdint>','#include <cstdint>\n#include <cstdio>')
old='auto finish=[&](int status){out[0]=labels.size();return status;};'
new='''auto finish=[&](int status){out[0]=labels.size();uint64_t live=0,occupied=0,maxfront=0,unequal=0;for(auto &l:labels)live+=l.live;for(auto &f:front){occupied+=!f.empty();maxfront=std::max(maxfront,uint64_t(f.size()));}for(uint64_t u=0;u<n;++u)for(uint64_t i=rows[u];i<rows[u+1];++i){auto v=dest[i];if(costs[i]!=UINT64_MAX&&capacities[v]&&other[v]<capacities[v])unequal+=(U(costs[i])*(U(other[v])+1)!=increments[i]);}std::fprintf(stderr,"RC_ACCOUNT status=%d allocated=%llu live=%llu occupied=%llu maxfront=%llu heap=%llu unequal_admissible_weights=%llu\\n",status,(unsigned long long)labels.size(),(unsigned long long)live,(unsigned long long)occupied,(unsigned long long)maxfront,(unsigned long long)heap.size(),(unsigned long long)unequal);return status;};'''
assert text.count(old)==1
cpp=out/'search.cpp';cpp.write_text(text.replace(old,new));libpath=out/'search.so'
subprocess.run(['g++','-O2','-std=c++17','-shared','-fPIC',str(cpp),'-o',str(libpath)],check=True)
base=ROOT/'experiments/mux_live_placement_updates_2026-10-06';case=json.loads((base/'protocol.json').read_text())['cases'][2]
inputs={str(p):sha(p) for p in (original,base/'w32/original_endpoints.json',base/'w32/swapped_endpoints.json',base/'w32/prediction.json',Path(case['source'])/'design.route')}
(out/'protocol.json').write_text(json.dumps(dict(inputs=inputs,source_sha256=sha(Path(__file__)),instrumented_sha256=sha(cpp),library_sha256=sha(libpath),policy='unchanged 1ns/10000/max4; observational counters only'),indent=2)+'\n')
ctx=PersistentRCContext(base/'w32/original_endpoints.json');state=import_native_ledger(ctx,Path(case['source'])/'design.route')
oldinit=NativeCapacityRC.__init__
def init(self,rc):
 oldinit(self,rc);signature=self.lib.rc_query.argtypes;self.lib=ctypes.CDLL(str(libpath));self.lib.rc_query.argtypes=signature;self.lib.rc_query.restype=ctypes.c_int
# Context already owns native search; swap only its library, preserving arrays and demand.
import inspect
native=[v for v in vars(ctx).values() if isinstance(v,NativeCapacityRC)]
assert len(native)==1
obj=native[0];signature=obj.lib.rc_query.argtypes;obj.lib=ctypes.CDLL(str(libpath));obj.lib.rc_query.argtypes=signature;obj.lib.rc_query.restype=ctypes.c_int
update=stage_reroute_with_repair(state,base/'w32/swapped_endpoints.json');candidate=update['repair'] or update['incremental']
frozen=json.loads((base/'w32/prediction.json').read_text())
assert candidate==frozen, 'instrumentation changed candidate'
assert all(sha(p)==h for p,h in inputs.items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),exact_frozen_candidate_equal=True,failure=candidate['failure'],completed=candidate['completed_connections']),indent=2)+'\n')
print('Exact frozen candidate parity verified',flush=True)
