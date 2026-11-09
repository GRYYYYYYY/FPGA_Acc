"""Instrument initialization state using frozen private v4 archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_remove_v4_2026-10-07'
r=json.loads((prior/'receipt.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256']
p=json.loads((prior/'protocol.json').read_text());assert r['protocol_sha256']==sha(prior/'protocol.json')
assert all(sha(f)==h for f,h in p['sources'].items())
out=ROOT/'build/native_resume_state_trace_v5_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
s=(prior/'source/route.cpp').read_text();s='#include <fstream>\n#include <iomanip>\n'+s
needle='        const char* remove_name = std::getenv("ROUTECAST_RESUME_REMOVE_NET");'
trace=r'''
        const char* trace_name = std::getenv("ROUTECAST_RESUME_STATE_TRACE");
        auto trace_state = [&](const char* stage) {
            if (!trace_name) return;
            std::ofstream stream(trace_name, std::ios::app);
            if (!stream) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot open resume state trace");
            stream << std::setprecision(17);
            for (auto node : device_ctx.rr_graph.nodes())
                stream << "O " << stage << " " << size_t(node) << " " << route_ctx.rr_node_route_inf[node].occ() << "\n";
            for (auto net : net_list.nets()) {
                if (route_ctx.route_trees[net]) {
                    for (auto& node : route_ctx.route_trees[net]->all_nodes())
                        stream << "T " << stage << " " << size_t(net) << " " << std::quoted(net_list.net_name(net)) << " " << size_t(node.inode) << " " << node.net_pin_index << "\n";
                }
                for (size_t pin=1; pin<net_list.net_pins(net).size(); ++pin)
                    stream << "D " << stage << " " << size_t(net) << " " << pin << " " << net_delay[net][pin] << "\n";
            }
            stream.flush();
            if (!stream) VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "Cannot write resume state trace");
        };
        trace_state("before");
'''
assert s.count(needle)==1;s=s.replace(needle,trace+needle)
needle='        timing_info->update();';assert s.count(needle)==1;s=s.replace(needle,'        trace_state("after");\n'+needle)
source=out/'source/route.cpp';source.write_text(s)
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr'
flags={}
for line in (shared/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'route.cpp.o';archive=out/'libvpr.a';exe=out/'routecast_resume_vpr'
compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
link=[str(exe) if x==str(prior/'routecast_resume_vpr') else str(archive) if x==str(prior/'libvpr.a') else x for x in p['link']]
inputs={str(prior/'libvpr.a'):sha(prior/'libvpr.a'),str(prior/'receipt.json'):sha(prior/'receipt.json'),str(prior/'protocol.json'):sha(prior/'protocol.json')}
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
