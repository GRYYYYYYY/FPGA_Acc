"""Read-only native in-memory RR/terminal snapshot hook; isolated object/link, shared inputs read-only."""
import json,subprocess,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();base=R/'build/native_candidate_retained_search_2026-10-06';inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';D=R/'build/native_resident_rr_snapshot_v2_2026-10-10';assert not D.exists();D.mkdir();S=D/'source';S.mkdir();p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());receipt=json.loads((base/'receipt.json').read_text());assert sha(base/'sequence_vpr')==receipt['binary_sha256'] and all(sha(f)==h for f,h in receipt['source_sha256'].items()) and all(sha(f)==h for f,h in receipt['shared_inputs_sha256'].items());bindings={str(f):sha(f) for f in [Path(__file__).resolve(),base/'source/route.cpp',base/'receipt.json',inputs/'libvpr.a',inputs/'read_route.o',inputs/'old_traceback.o',inputs/'sync_once.o']};bindings.update(receipt['shared_inputs_sha256'])
s=(base/'source/route.cpp').read_text();needle='    const bool retained_input=routecast_retained_pending;'
hook=r'''    if (const char* snapshot = std::getenv("ROUTECAST_RESIDENT_SNAPSHOT")) {
        if (is_flat) throw std::runtime_error("resident snapshot rejects flat mode");
        FILE* fp=std::fopen(snapshot,"w");
        if(!fp) throw std::runtime_error("cannot open resident snapshot");
        const auto& rr=device_ctx.rr_graph;
        std::fprintf(fp,"H\t1\t%zu\n",rr.num_nodes());
        size_t edges=0,pins=0,nets=0;
        for(auto node:rr.nodes()) {
            std::fprintf(fp,"N\t%zu\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%a\t%a\n",size_t(node),int(rr.node_type(node)),int(rr.node_capacity(node)),int(rr.node_xlow(node)),int(rr.node_xhigh(node)),int(rr.node_ylow(node)),int(rr.node_yhigh(node)),int(rr.node_layer(node)),double(rr.node_R(node)),double(rr.node_C(node)));
            for(auto edge:rr.edges(node)) {
                std::fprintf(fp,"E\t%zu\t%zu\t%d\n",size_t(node),size_t(rr.edge_sink_node(node,edge)),int(rr.edge_switch(node,edge)));++edges;
            }
        }
        for(size_t sid=0;sid<device_ctx.rr_switch_inf.size();++sid) {
            const auto& sw=device_ctx.rr_switch_inf[sid];
            std::fprintf(fp,"S\t%zu\t%a\t%a\n",sid,double(sw.R),double(sw.Tdel));
        }
        for(auto net:net_list.nets()) {
            const auto& name=net_list.net_name(net);
            if(name.find_first_of("\t\r\n")!=std::string::npos) {std::fclose(fp);throw std::runtime_error("snapshot NET name contains control separator");}
            std::fprintf(fp,"T\t%zu\t%d\t%zu\t%s\n",size_t(net),int(net_list.net_is_ignored(net)),net_list.net_pins(net).size(),name.c_str());++nets;
            for(size_t pin=0;pin<net_list.net_pins(net).size();++pin) {
                std::fprintf(fp,"P\t%zu\t%zu\t%zu\n",size_t(net),pin,size_t(route_ctx.net_rr_terminals[net][pin]));++pins;
            }
        }
        std::fprintf(fp,"F\t%zu\t%zu\t%zu\n",edges,nets,pins);
        const bool failed=std::ferror(fp);const int closed=std::fclose(fp);
        if(failed || closed)throw std::runtime_error("resident snapshot write failed");
        VTR_LOG("ROUTECAST readonly resident snapshot nodes=%zu edges=%zu nets=%zu pins=%zu\n",rr.num_nodes(),edges,nets,pins);
    }
'''
assert s.count(needle)==1;s=s.replace(needle,hook+needle);(S/'route.cpp').write_text(s);(S/'build.py').write_text(Path(__file__).read_text());obj=D/'route.o';cmd=[*p['compile'][:-4],'-c',str(S/'route.cpp'),'-o',str(obj)]
with (D/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(obj),str(inputs/'sync_once.o'),wrap]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(f)==h for f,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),source_sha256={str(f):sha(f) for f in S.iterdir()},scope='Only environment-gated read-only resident graph+allNETterminal snapshot inserted after init_route_structs before seed import. Does not reuse predictor state or establish netgain.'),indent=2)+'\n');print('RESIDENT SNAPSHOT BUILT')
