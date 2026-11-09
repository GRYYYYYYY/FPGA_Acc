"""Private non-semantic CBRR instrumentation on frozen resume archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_cbrr_force_audit_v2_2026-10-07';r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256'] and sha(prior/'protocol.json')==r['protocol_sha256']
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';file=ROOT/'build/native_resume_cbrr_growth_audit_2026-10-07/source/route.cpp'
out=ROOT/'build/native_resume_best_state_audit_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
s=file.read_text()
needle='    RoutingMetrics best_routing_metrics;'
trace=r"""
    auto rc_dump_delays = [&](const char* stage, int iteration) {
        if (!std::getenv("ROUTECAST_BEST_STATE_AUDIT")) return;
        VTR_LOG("RC_BEST_CPD %s %d %.9g\n", stage, iteration, double(timing_info->least_slack_critical_path().delay()));
        for (auto net : net_list.nets()) {
            if (!route_ctx.route_trees[net]) continue;
            for (unsigned pin = 1; pin < net_list.net_pins(net).size(); ++pin) {
                auto sink = route_ctx.route_trees[net]->find_by_isink(pin);
                if (sink) VTR_LOG("RC_BEST_DELAY %s %d %zu %s %u %.9g %.9g\n", stage, iteration, size_t(net), net_list.net_name(net).c_str(), pin, double(net_delay[net][pin]), double(sink->Tdel));
            }
        }
    };
"""
assert s.count(needle)==1;s=s.replace(needle,needle+trace)
for needle,extra in [
('        critical_path = timing_info->least_slack_critical_path();','\n        rc_dump_delays("iteration", itry);'),
('                best_routing = router_ctx.route_trees;','\n                rc_dump_delays("save", itry);'),
('        router_ctx.route_trees = best_routing;','\n        rc_dump_delays("restored", itry);'),
('        prune_unused_non_configurable_nets(connections_inf, net_list);','\n        rc_dump_delays("pruned", itry);')]:
 assert s.count(needle)==1;s=s.replace(needle,needle+extra)
source=out/'source/route.cpp';source.write_text(s)
shared=up/'build_tileplace_vpr/vpr';flags={}
for line in (shared/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'route.cpp.o';archive=out/'libvpr.a';exe=out/'routecast_resume_vpr'
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
