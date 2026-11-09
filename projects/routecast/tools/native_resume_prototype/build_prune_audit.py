"""Private non-semantic CBRR instrumentation on frozen resume archive."""
import json,shlex,shutil,subprocess,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];prior=ROOT/'build/native_resume_cbrr_tol101_force_audit_2026-10-07';r=json.loads((prior/'receipt.json').read_text());p=json.loads((prior/'protocol.json').read_text());assert sha(prior/'libvpr.a')==r['private_archive_sha256'] and sha(prior/'protocol.json')==r['protocol_sha256']
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';file=prior/'source/connection_based_routing.cpp'
out=ROOT/'build/native_resume_prune_audit_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
sources=[]
for name in ('route_net.cpp','route.cpp'):
 file=ROOT/'build/native_resume_target_partial_v7_2026-10-07/source'/name
 code=file.read_text()
 trace=r"""
    auto rc_dump_tree = [&](const char* stage, int iteration, ParentNetId net) {
        if (!std::getenv("ROUTECAST_PRUNE_AUDIT") || net_list.net_name(net) != "s6_0") return;
        const auto& ctx = g_vpr_ctx.routing();
        if (!ctx.route_trees[net]) return;
        for (const auto& node : ctx.route_trees[net]->all_nodes()) {
            auto parent = node.parent();
            VTR_LOG("RC_PRUNE %s %d %zu %d %ld %zu %d %.9g\n", stage, iteration, size_t(net), node.net_pin_index, parent ? long(size_t(parent->inode)) : -1L, size_t(node.inode), ctx.rr_node_route_inf[node.inode].occ(), double(node.Tdel));
        }
    };
"""
 if name=='route_net.cpp':
  needle='    bool ripup_high_fanout_nets = check_hold(router_opts, worst_neg_slack);'
  assert code.count(needle)==1;code=code.replace(needle,trace+'\n    rc_dump_tree("before", itry, net_id);\n'+needle)
  needle='    // completed constructing the partial route tree and updated all other data structures to match'
  assert code.count(needle)==1;code=code.replace(needle,'    rc_dump_tree("after", itry, net_id);\n'+needle)
 else:
  needle='    RoutingMetrics best_routing_metrics;'
  assert code.count(needle)==1;code=code.replace(needle,needle+trace)
  needle='        critical_path = timing_info->least_slack_critical_path();'
  assert code.count(needle)==1;code=code.replace(needle,needle+'\n        for (auto net : net_list.nets()) rc_dump_tree("routed", itry, net);')
 source=out/'source'/name;source.write_text(code);sources.append(source)
shared=up/'build_tileplace_vpr/vpr';flags={}
for line in (shared/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'route_net.cpp.o';archive=out/'libvpr.a';exe=out/'routecast_resume_vpr'
compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
link=[str(exe) if x==str(prior/'routecast_resume_vpr') else str(archive) if x==str(prior/'libvpr.a') else x for x in p['link']]
inputs={str(prior/'libvpr.a'):sha(prior/'libvpr.a'),str(prior/'receipt.json'):sha(prior/'receipt.json'),str(file):sha(file)}
inputs.update({x:sha(x) for x in link if x.endswith(('.a','.o')) and x!=str(archive)})
protocol=dict(inputs=inputs,source_sha256={str(f):sha(f) for f in sources},builder_sha256=sha(Path(__file__)),compile=compile,link=link)
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
shutil.copyfile(prior/'libvpr.a',archive)
for source in sources:
 obj=out/(source.name+'.o');compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
 with (out/'compile.log').open('a') as log:result=subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 if result.returncode:raise SystemExit(result.returncode)
 subprocess.run(['ar','r',str(archive),str(obj)],check=True)
for cmd in (['ranlib',str(archive)],link):
 with (out/'link.log').open('a') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 if result.returncode:raise SystemExit(result.returncode)
assert all(sha(f)==h for f,h in inputs.items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),binary_sha256=sha(exe),private_archive_sha256=sha(archive),build_seconds=time.perf_counter()-start),indent=2)+'\n');print(exe)
