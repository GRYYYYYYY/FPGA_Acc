"""Owned connection-router translation unit, vendor inputs remain read-only."""
import json,subprocess,shlex,shutil
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_connection_query_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_native_query_probe_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';native=vendor/'vpr/src/route/connection_router.cpp';s=native.read_text();needle='    conn_params_ = &conn_params;';assert s.count(needle)==3
 declaration='''
extern "C" void routecast_connection_begin(const RouteTreeNode&,RRNodeId,const ConnectionParameters&);
extern "C" void routecast_connection_end();
struct RouteCastConnectionScope { RouteCastConnectionScope(const RouteTreeNode& root,RRNodeId sink,const ConnectionParameters& params){routecast_connection_begin(root,sink,params);} ~RouteCastConnectionScope(){routecast_connection_end();} };
'''
 s=s.replace('/** return tuple <found_path',declaration+'\n/** return tuple <found_path',1).replace(needle,needle+'\n    RouteCastConnectionScope routecast_scope(rt_root,sink_node,conn_params);',2)
 # all-shortest-paths third entry has no sink_node; use invalid sentinel.
 pos=s.rfind(needle);s=s[:pos]+s[pos:].replace(needle,needle+'\n    RouteCastConnectionScope routecast_scope(rt_root,RRNodeId::INVALID(),conn_params);',1)
 cs=D/'connection_router.cpp';cs.write_text(s)
 observer=(old/'observer.cpp').read_text();observer=observer.replace('using QueryKey=std::array<uint64_t,10>;','static thread_local uint64_t connection_id=0,connection_pin=0,connection_sink=0;\nstatic thread_local bool connection_active=false;\nstatic thread_local std::set<size_t> connection_owned;\nusing QueryKey=std::array<uint64_t,15>;')
 observer=observer.replace('#include <array>','#include <array>\n#include <set>')
 observer=observer.replace('uint64_t(rt.non_configurable_bitset.get(node))}}','uint64_t(rt.non_configurable_bitset.get(node)),uint64_t(connection_active),connection_id,connection_pin,connection_sink,uint64_t(connection_owned.count(size_t(node)))}}')
 observer+='''
extern "C" void routecast_connection_begin(const RouteTreeNode& root,RRNodeId sink,const ConnectionParameters& params){
 if(connection_active)throw std::runtime_error("nested connection scope");
 connection_active=true;++connection_id;connection_pin=params.target_pin_num_;connection_sink=size_t(sink);connection_owned.clear();
 connection_owned.insert(size_t(root.inode));for(const auto& node:root.all_nodes())connection_owned.insert(size_t(node.inode));
 if(query_net!=int(size_t(params.net_id_)))throw std::runtime_error("connection NET marker mismatch");
 const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream out(std::string(path)+".connections.tsv",std::ios::app);out<<phase_iteration+1<<'\\t'<<connection_id<<'\\t'<<size_t(params.net_id_)<<'\\t'<<connection_pin<<'\\t'<<connection_sink<<'\\t'<<connection_owned.size()<<'\\n';if(!out)throw std::runtime_error("connection write");}
}
extern "C" void routecast_connection_end(){if(!connection_active)throw std::runtime_error("connection close mismatch");connection_active=false;connection_owned.clear();}
'''
 op=D/'observer.cpp';op.write_text(observer);oc=p['compile'].copy();oc[oc.index('-c')+1]=str(op);oc[oc.index('-o')+1]=str(D/'observer.o')
 flags=vendor/'build_tileplace_vpr/vpr/CMakeFiles/libvpr.dir/flags.make';opts={line.split(' = ',1)[0]:shlex.split(line.split(' = ',1)[1]) for line in flags.read_text().splitlines() if ' = ' in line};cc=['/usr/bin/c++',*opts['CXX_DEFINES'],*opts['CXX_INCLUDES'],*opts['CXX_FLAGS'],'-c',str(cs),'-o',str(D/'connection_router.cpp.o')]
 link=p['link'].copy();link=[str(D/'observer.o') if a==str(old/'observer.o') else a for a in link];link[link.index('-o')+1]=str(D/'vpr');archive=next(Path(x) for x in link if x.endswith('/libvpr.a'));owned=D/'libvpr.a';shutil.copyfile(archive,owned);link=[str(owned) if x==str(archive) else x for x in link]
 bindings={str(x):sha(x) for x in [Path(__file__),old/'protocol.json',native,flags,archive,cs,op]};(D/'protocol.json').write_text(json.dumps(dict(compile=oc,connection_compile=cc,link=link,bindings=bindings,scope='Owned source copy adds RAII connection scope at three native entry functions; copied archive replaces only connection_router.cpp.o. Shared vendor unchanged. Native routing expressions unchanged; parity pending.'),indent=2)+'\n')
 for name,cmd in [('connection_compile',cc),('observer_compile',oc),('archive_replace',['ar','r',str(owned),str(D/'connection_router.cpp.o')]),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',owned,D/'observer.o',D/'connection_router.cpp.o']}),indent=2)+'\n')
if __name__=='__main__':main()
