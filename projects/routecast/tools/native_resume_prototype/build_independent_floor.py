"""Private non-semantic CBRR instrumentation on frozen resume archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_ungated_wholenet_2026-10-07';r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256'] and sha(prior/'protocol.json')==r['protocol_sha256']
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';file=ROOT/'build/native_resume_cbrr_tol101_2026-10-07/source/connection_based_routing.cpp'
out=ROOT/'build/native_resume_independent_floor_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
s='#include <fstream>\n#include <map>\n#include <set>\n#include <cmath>\n#include <stdexcept>\n#include "globals.h"\n#include "vpr_context.h"\n'+file.read_text()
needle='void Connection_based_routing_resources::set_lower_bound_connection_delays(NetPinsMatrix<float>& net_delay) {'
trace=r"""
    std::map<std::pair<size_t,size_t>, double> rc_floors;
    std::set<std::pair<size_t,size_t>> rc_used;
    const char* rc_file = std::getenv("ROUTECAST_RR_FLOORS_FILE");
    if (rc_file) {
        std::ifstream input(rc_file); std::string tag, digest; size_t nodes, count;
        if (!(input >> tag >> digest >> nodes >> count) || tag != "ROUTECAST_FLOORS_SECONDS_V1" || digest.size()!=64 || nodes != g_vpr_ctx.device().rr_graph.num_nodes()) throw std::runtime_error("floor header mismatch");
        for(size_t i=0;i<count;++i) {
            size_t source,sink; double seconds;
            if (!(input >> source >> sink >> seconds) || source>=nodes || sink>=nodes || !std::isfinite(seconds) || seconds<0 || !std::isfinite(float(seconds)) || !rc_floors.emplace(std::make_pair(source,sink),seconds).second) throw std::runtime_error("floor row invalid");
        }
        std::string extra; if(input >> extra) throw std::runtime_error("floor trailing data");
        VTR_LOG("RC_FLOORS_LOADED %zu %s\n", rc_floors.size(), digest.c_str());
    }
"""
assert s.count(needle)==1;s=s.replace(needle,needle+trace)
needle='            net_lower_bound_connection_delay[ipin] = net_delay[net_id][ipin];'
trace=r"""
            if (rc_file && !net_list_.net_is_ignored(net_id)) {
                auto key=std::make_pair(size_t(net_terminals_[net_id][0]),size_t(net_terminals_[net_id][ipin]));
                auto floor=rc_floors.find(key); if(floor==rc_floors.end()) throw std::runtime_error("floor endpoint coverage mismatch");
                float value=std::nextafter(float(floor->second),0.f);
                net_lower_bound_connection_delay[ipin]=std::min(net_lower_bound_connection_delay[ipin],value);
                rc_used.insert(key);
                VTR_LOG("RC_FLOOR_BIND %zu %s %u %zu %zu %.9g %.9g\n",size_t(net_id),net_list_.net_name(net_id).c_str(),ipin,key.first,key.second,double(net_delay[net_id][ipin]),double(net_lower_bound_connection_delay[ipin]));
            }
"""
assert s.count(needle)==1;s=s.replace(needle,needle+trace)
needle='\nvoid Connection_based_routing_resources::update_lower_bound_connection_delay'
a=s.index(needle);before=s[:a];assert before.endswith('}\n')
before=before[:-2]+'    if (rc_file && rc_used.size()!=rc_floors.size()) throw std::runtime_error("unused floor endpoints");\n}\n';s=before+s[a:]
source=out/'source/connection_based_routing.cpp';source.write_text(s)
shared=up/'build_tileplace_vpr/vpr';flags={}
for line in (shared/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'connection_based_routing.cpp.o';archive=out/'libvpr.a';exe=out/'routecast_resume_vpr'
compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
link=[str(exe) if x==str(prior/'routecast_resume_vpr') else str(archive) if x==str(prior/'libvpr.a') else x for x in p['link']]
inputs={str(prior/'libvpr.a'):sha(prior/'libvpr.a'),str(prior/'receipt.json'):sha(prior/'receipt.json'),str(file):sha(file)}
inputs.update({x:sha(x) for x in link if x.endswith(('.a','.o')) and x!=str(archive)})
protocol=dict(inputs=inputs,source_sha256=sha(source),builder_sha256=sha(Path(__file__)),compile=compile,link=link)
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
with (out/'compile.log').open('w') as log:result=subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,timeout=180)
if result.returncode:raise SystemExit(result.returncode)
shutil.copyfile(prior/'libvpr.a',archive)
for cmd in (['ar','r',str(archive),str(obj)],['ranlib',str(archive)],link):
 with (out/'link.log').open('a') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 if result.returncode:raise SystemExit(result.returncode)
assert all(sha(f)==h for f,h in inputs.items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),binary_sha256=sha(exe),private_archive_sha256=sha(archive),build_seconds=time.perf_counter()-start),indent=2)+'\n');print(exe)
