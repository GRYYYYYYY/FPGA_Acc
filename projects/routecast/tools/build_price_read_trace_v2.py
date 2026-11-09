"""Isolated instrumentation: replace every price subscript with an exact-value read."""
from pathlib import Path
import re,hashlib,json,subprocess
R=Path(__file__).resolve().parents[1]; O=R/'build/price_read_trace_v2_2026-10-10';O.mkdir(exist_ok=True)
inputs={};outputs={}
helper='''
#include <cstdint>
#include <vector>
static thread_local std::vector<uint64_t> rc_reads;
static thread_local uint64_t rc_read_limit=65536;
static thread_local bool rc_read_complete=true;
static inline uint64_t rc_price_read(const uint64_t* p,uint64_t u){
 if(rc_read_complete){if(rc_reads.size()>=rc_read_limit)rc_read_complete=false;
 else try{rc_reads.push_back(u);}catch(...){rc_read_complete=false;}}
 return p[u];
}
extern "C" void rc_reads_begin(uint64_t limit){rc_read_limit=limit;rc_reads.clear();rc_read_complete=true;}
extern "C" int rc_reads_complete(){return rc_read_complete;}
extern "C" void rc_reads_clear(){rc_reads.clear();}
extern "C" uint64_t rc_reads_count(){return rc_reads.size();}
extern "C" uint64_t rc_reads_at(uint64_t i){return rc_reads.at(i);}
'''
for name in ['tree_workspace_radix_v3.cpp','tree_workspace_radix_stats_v4.cpp','bidirectional_workspace_v2.cpp']:
 p=R/'tools/soft_demand_cpp'/name;original=p.read_text();inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();s=original
 for expression in ['w->dest[x]','w->dest[e]','destination','v']:
  s=s.replace('price['+expression+']','rc_price_read(price,'+expression+')')
 assert 'price[' not in s
 assert s.replace('rc_price_read(price,w->dest[x])','price[w->dest[x]]').replace('rc_price_read(price,w->dest[e])','price[w->dest[e]]').replace('rc_price_read(price,destination)','price[destination]').replace('rc_price_read(price,v)','price[v]')==original
 # Included stats kernel must share the helper declared by the bidi translation unit.
 if name!='tree_workspace_radix_stats_v4.cpp':s=helper+s
 (O/name).write_text(s)
for name,lib in [('tree_workspace_radix_v3.cpp','forward.so'),('bidirectional_workspace_v2.cpp','bidi.so')]:
 p=subprocess.run(['g++','-std=c++17','-O3','-shared','-fPIC',str(O/name),'-o',str(O/lib)],capture_output=True,text=True);(O/(lib+'.build.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
 outputs[str(O/lib)]=hashlib.sha256((O/lib).read_bytes()).hexdigest()
for p in O.glob('*.cpp'):outputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in inputs.items())
(O/'receipt.json').write_text(json.dumps(dict(inputs=inputs,outputs=outputs,scope='128bit standalone kernels only; exact read-value substitution, bounded diagnostic transcript with incomplete flag; not native64 cache'),indent=2)+'\n')
print('TRACE BUILD PASS')
