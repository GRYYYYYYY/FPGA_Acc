"""Isolated copied-header observer; no changes to archived or sibling source."""
import json,sys,shutil,subprocess,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
D=R/'build/native_external_initial_response_observer_v1_2026-10-19'
def main():
 P=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());base=R/'build/native_candidate_move_accept_scoped_2026-10-06';original=R/'build/native_candidate_retained_search_2026-10-06/source/route.cpp';vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route';D.mkdir(exist_ok=False);src=D/'source';src.mkdir();overlay=src/'overlay';overlay.mkdir();bindings={str(original):sha(original),str(Path(__file__).resolve()):sha(__file__)}
 for f in vendor.iterdir():
  if f.suffix in ['.h','.tpp']:shutil.copyfile(f,overlay/f.name);bindings[str(f)]=sha(f)
 s=original.read_text();anchor='        print_router_criticality_histogram(net_list, *timing_info, netlist_pin_lookup, is_flat);';assert s.count(anchor)==2
 code=r'''
        FILE* obs=std::fopen("initial_connections.tsv","wx");
        if(!obs)throw std::runtime_error("observer initial open");
        std::fprintf(obs,"net\tpin\tsource_rr\tsink_rr\tdelay_s\tcriticality\n");
        for(auto net:net_list.nets()) {
            if(net_list.net_is_ignored(net))continue;
            for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                float crit=calculate_clb_net_pin_criticality(*timing_info,netlist_pin_lookup,net_list.net_pin(net,pin),is_flat);
                std::fprintf(obs,"%zu\t%zu\t%zu\t%zu\t%.9g\t%.9g\n",size_t(net),pin,size_t(route_ctx.net_rr_terminals[net][0]),size_t(route_ctx.net_rr_terminals[net][pin]),double(net_delay[net][pin]),double(crit));
            }
        }
        if(std::fclose(obs))throw std::runtime_error("observer initial close");
'''
 s=s.replace(anchor,anchor+code,1);anchor2='        RouteIterResults iter_results = netlist_router->route_netlist(itry, pres_fac, worst_negative_slack);';assert s.count(anchor2)==1;s=s.replace(anchor2,anchor2+r'''
        if(itry==1) {
            FILE* first=std::fopen("first_iteration.route","wx");
            if(!first)throw std::runtime_error("observer tree open");
            print_route(net_list,first,is_flat);
            if(std::fclose(first))throw std::runtime_error("observer tree close");
        }
''');(src/'route.cpp').write_text(s)
 t=overlay/'SerialNetlistRouter.tpp';text=t.read_text();anchor3='        ParentNetId net_id = sorted_nets[inet];';assert text.count(anchor3)==1;text=text.replace(anchor3,anchor3+'\n        if(itry==1)VTR_LOG("RC_FIRST_NET_ORDER %zu %zu\\n",inet,size_t(net_id));');t.write_text(text)
 compile=[P['compile'][0],'-I'+str(overlay),*P['compile'][1:-4],'-c',str(src/'route.cpp'),'-o',str(D/'route.o')]
 link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in P['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(D/'route.o'),str(base/'sync_once.o'),wrap]
 for x in link:
  if Path(x).is_file():bindings[x]=sha(x)
 for f in src.rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Initial lookahead delay and production setup-criticality only; no direct hold criticality export. Runtime actual NET invocation order and first iteration printed trees. Read-only observer; runtime equivalence pending.'),indent=2)+'\n')
 assert all(sha(p)==h for p,h in bindings.items())
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='OBSERVER_BUILT_RUNTIME_EQUIVALENCE_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('OBSERVER_BUILT')
if __name__=='__main__':main()
