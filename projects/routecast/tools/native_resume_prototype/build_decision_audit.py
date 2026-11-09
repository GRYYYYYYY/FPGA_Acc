"""Private non-semantic CBRR instrumentation on frozen resume archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_ungated_wholenet_2026-10-07';r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256'] and sha(prior/'protocol.json')==r['protocol_sha256']
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';file=ROOT/'build/native_resume_cbrr_tol101_2026-10-07/source/connection_based_routing.cpp'
out=ROOT/'build/native_resume_decision_audit_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
s=file.read_text()
needle='    bool any_connection_rerouted = false;'
assert s.count(needle)==1;s=s.replace(needle,'    static unsigned rc_call = 0;\n    if (std::getenv("ROUTECAST_DECISION_AUDIT")) VTR_LOG("RC_DECISION_CALL %u\\n", ++rc_call);\n'+needle)
needle='            auto rr_sink_node = net_terminals_[net_id][ipin];'
trace=r"""
            auto rc_log = [&](const char* reason, float criticality) {
                if (std::getenv("ROUTECAST_DECISION_AUDIT")) VTR_LOG("RC_DECISION %u %zu %s %d %zu %s %.9g %.9g %.9g %.9g %.9g\n", rc_call, size_t(net_id), net_list_.net_name(net_id).c_str(), ipin, size_t(rr_sink_node), reason, double(net_delay[net_id][ipin]), double(lower_bound_connection_delay[net_id][ipin]), double(criticality), double(max_criticality * connection_criticality_tolerance), double(connection_delay_optimality_tolerance));
            };
"""
# Constructor has a similar terminal lookup; use the occurrence in force routine only.
a=s.index('bool Connection_based_routing_resources::forcibly_reroute_connections');prefix=s[:a];body=s[a:];assert body.count(needle)==1;body=body.replace(needle,needle+trace)
body=body.replace('            if (lower_bound_connection_delay[net_id][ipin] == 0)\n                continue;', '            if (lower_bound_connection_delay[net_id][ipin] == 0) { rc_log("zero", -1.f); continue; }')
needle='                lower_bound_connection_delay[net_id][ipin] = net_delay[net_id][ipin];'
assert body.count(needle)==1;body=body.replace(needle,'                rc_log("improved", -1.f);\n'+needle)
needle='            if (pin_criticality < (max_criticality * connection_criticality_tolerance))\n                continue;'
assert body.count(needle)==1;body=body.replace(needle,'            if (pin_criticality < (max_criticality * connection_criticality_tolerance)) { rc_log("criticality", pin_criticality); continue; }')
needle='            if (net_delay[net_id][ipin] < (lower_bound_connection_delay[net_id][ipin] * connection_delay_optimality_tolerance))\n                continue;'
assert body.count(needle)==1;body=body.replace(needle,'            if (net_delay[net_id][ipin] < (lower_bound_connection_delay[net_id][ipin] * connection_delay_optimality_tolerance)) { rc_log("delay", pin_criticality); continue; }')
needle='            forcible_reroute_connection_flag[net_id][rr_sink_node] = true;'
assert body.count(needle)==1;body=body.replace(needle,'            rc_log("selected", pin_criticality);\n'+needle)
s=prefix+body
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
