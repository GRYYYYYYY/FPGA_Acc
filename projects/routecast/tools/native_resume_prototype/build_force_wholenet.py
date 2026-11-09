"""Private non-semantic CBRR instrumentation on frozen resume archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_cbrr_tol101_2026-10-07';r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256'] and sha(prior/'protocol.json')==r['protocol_sha256']
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';file=ROOT/'build/native_resume_target_partial_v7_2026-10-07/source/route_net.cpp'
out=ROOT/'build/native_resume_force_wholenet_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
s=file.read_text()
needle='    bool ripup_high_fanout_nets = check_hold(router_opts, worst_neg_slack);'
trace=r"""
    bool rc_force_whole_net = false;
    if (tree) {
        for (unsigned pin = 1; pin < net_list.net_pins(net_id).size(); ++pin) {
            auto sink = tree->find_by_isink(pin);
            if (sink && connections_inf.should_force_reroute_connection(net_id, sink->inode)) {
                rc_force_whole_net = true;
                break;
            }
        }
    }
    if (rc_force_whole_net) VTR_LOG("RC_FORCE_WHOLE_NET %d %zu %s\n", itry, size_t(net_id), net_list.net_name(net_id).c_str());
"""
assert s.count(needle)==1;s=s.replace(needle,trace+needle)
needle='|| ripup_high_fanout_nets) {'
assert s.count(needle)==1;s=s.replace(needle,'|| ripup_high_fanout_nets || rc_force_whole_net) {')
source=out/'source/route_net.cpp';source.write_text(s)
shared=up/'build_tileplace_vpr/vpr';flags={}
for line in (shared/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'route_net.cpp.o';archive=out/'libvpr.a';exe=out/'routecast_resume_vpr'
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
