"""Only log original criticality return values; all router objects remain frozen."""
import json,subprocess,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();B=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';D=R/'build/native_criticality_observer_v1_2026-10-10';D.mkdir();b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['source_sha256'].items())
inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';nm=subprocess.check_output(['nm',str(inputs/'libvpr.a')],text=True);symbols=[line.split()[-1] for line in nm.splitlines() if ' T _Z23get_net_pin_criticality' in line];assert len(symbols)==1;symbol=symbols[0]
source='''#include "globals.h"
#include "route_net.h"
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
extern "C" float REAL(const SetupHoldTimingInfo*,const ClusteredPinAtomPinsLookup&,float,float,ParentNetId,ParentPinId,bool);
struct Writer {
 FILE* fp=nullptr;unsigned long long sequence=0;
 Writer(){if(const char* p=std::getenv("ROUTECAST_CRITICALITY_TRACE")){fp=std::fopen(p,"w");if(!fp)throw std::runtime_error("criticality trace open");}}
 ~Writer(){if(fp){bool failed=std::ferror(fp);int code=std::fclose(fp);if(failed || code)std::abort();}}
};
extern "C" float WRAP(const SetupHoldTimingInfo* timing,const ClusteredPinAtomPinsLookup& lookup,float maximum,float exponent,ParentNetId net,ParentPinId pin,bool flat){
 float result=REAL(timing,lookup,maximum,exponent,net,pin,flat);
 static Writer writer;
 if(writer.fp){
  if(flat)throw std::runtime_error("criticality trace requires clustered mode");
  const auto& list=g_vpr_ctx.clustering().clb_nlist;ClusterPinId id{size_t(pin)};
  if(size_t(list.pin_net(id))!=size_t(net))throw std::runtime_error("criticality pin NET mismatch");
  std::fprintf(writer.fp,"C\\t%llu\\t%zu\\t%zu\\t%d\\t%.9g\\t%.9g\\t%.9g\\n",++writer.sequence,size_t(net),size_t(pin),list.pin_net_index(id),double(result),double(maximum),double(exponent));
 }
 return result;
}
'''.replace('REAL','__real_'+symbol).replace('WRAP','__wrap_'+symbol)
(D/'observer.cpp').write_text(source)
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());compile=[*p['compile'][:-4],'-c',str(D/'observer.cpp'),'-o',str(D/'observer.o')]
with (D/'compile.log').open('w') as log:subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,check=True)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(B/'route.o'),str(inputs/'sync_once.o'),str(D/'observer.o'),wrap,'-Wl,--wrap='+symbol]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
files=[Path(__file__),B/'receipt.json',B/'route.o',inputs/'libvpr.a',D/'observer.cpp',D/'observer.o']
bindings={**b['bindings'],**b['source_sha256'],**{str(p.resolve()):sha(p) for p in files}}
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),symbol=symbol,compile=compile,link=link,scope='Original criticality function called once per wrapper invocation; original float returned unchanged. Runtime call coverage/output identity unproven until trial.'),indent=2)+'\n');print('CRITICALITY OBSERVER BUILD PASS')
