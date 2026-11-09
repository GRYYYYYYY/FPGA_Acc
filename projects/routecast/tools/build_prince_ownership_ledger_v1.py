"""Independent CHANNEL owner ledger from original native tree occupancy updates."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_ownership_ledger_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_connection_query_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());s=(old/'observer.cpp').read_text()
 decl='''
static void ledger_query(RRNodeId);
static void ledger_entry(const RouteTreeNode&,const ConnectionParameters&);
static void ledger_boundary(int);
static uint64_t query_calls=0,query_channel_calls=0,query_owned_calls=0,query_digest=14695981039346656037ULL;
'''
 s=s.replace('using QueryKey=std::array<uint64_t,15>;',decl+'\nusing QueryKey=std::array<uint64_t,15>;')
 s=s.replace(' ++query_rows[key];',' ledger_query(node);++query_calls;if(d.rr_graph.node_type(node)==CHANX||d.rr_graph.node_type(node)==CHANY){++query_channel_calls;query_owned_calls+=connection_owned.count(size_t(node));}for(auto word:key)hash_word<uint64_t>(query_digest,word);')
 s=s.replace(' query_net=-1;__real__Z9setup_net',' query_net=int(size_t(net));__real__Z9setup_net')
 oldflush='const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream out(path,std::ios::app);for(const auto& row:query_rows){out<<iteration;for(auto x:row.first)out<<\'\\t\'<<x;out<<\'\\t\'<<row.second<<\'\\n\';}if(!out)throw std::runtime_error("query trace write");}'
 newflush='const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream out(path,std::ios::app);out<<iteration<<\'\\t\'<<query_calls<<\'\\t\'<<query_channel_calls<<\'\\t\'<<query_owned_calls<<\'\\t\'<<query_digest<<\'\\n\';if(!out)throw std::runtime_error("query trace write");}ledger_boundary(iteration);query_calls=query_channel_calls=query_owned_calls=0;query_digest=14695981039346656037ULL;'
 assert oldflush in s;s=s.replace(oldflush,newflush)
 s=s.replace(' const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream out(std::string(path)+".connections.tsv"', ' ledger_entry(root,params);\n const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream out(std::string(path)+".connections.tsv"')
 helper='''
static std::map<size_t,std::set<size_t>> ledger_owners;
static std::map<size_t,int> ledger_counts;
static uint64_t ledger_epoch=0;
static bool channel(size_t node){auto type=g_vpr_ctx.device().rr_graph.node_type(RRNodeId(node));return type==CHANX||type==CHANY;}
static std::ofstream& ledger_stream(){static std::ofstream f(std::string(std::getenv("ROUTECAST_QUERY_FILE"))+".ledger.bin",std::ios::binary);if(!f)throw std::runtime_error("ledger open");return f;}
static void ledger_word(uint64_t value){put<uint64_t>(ledger_stream(),value);}
extern "C" void __real__Z38pathfinder_update_cost_from_route_treeRK13RouteTreeNodei(const RouteTreeNode&,int);
extern "C" void __wrap__Z38pathfinder_update_cost_from_route_treeRK13RouteTreeNodei(const RouteTreeNode& root,int delta){
 std::set<size_t> nodes;if(std::getenv("ROUTECAST_QUERY_FILE")){if(channel(size_t(root.inode)))nodes.insert(size_t(root.inode));for(const auto& n:root.all_nodes())if(channel(size_t(n.inode)))nodes.insert(size_t(n.inode));}
 __real__Z38pathfinder_update_cost_from_route_treeRK13RouteTreeNodei(root,delta);
 if(!std::getenv("ROUTECAST_QUERY_FILE"))return;
 if(!query_scope||query_net<0||connection_active||(delta!=1&&delta!=-1))throw std::runtime_error("ledger update context");
 ++ledger_epoch;auto& own=ledger_owners[size_t(query_net)];
 for(auto n:nodes){if(delta==1){if(!own.insert(n).second)throw std::runtime_error("duplicate ledger owner add");}else if(own.erase(n)!=1)throw std::runtime_error("missing ledger owner remove");ledger_counts[n]+=delta;if(ledger_counts[n]<0||ledger_counts[n]!=g_vpr_ctx.routing().rr_node_route_inf[RRNodeId(n)].occ())throw std::runtime_error("native update occupancy mismatch");}
 ledger_word(1);ledger_word(ledger_epoch);ledger_word(query_net);ledger_word(delta==1?1:0);ledger_word(nodes.size());for(auto n:nodes)ledger_word(n);
}
static void ledger_query(RRNodeId node){
 if(!connection_active||query_net<0)throw std::runtime_error("cost call outside connection");
 if(channel(size_t(node))){size_t n=size_t(node);if(ledger_counts[n]!=g_vpr_ctx.routing().rr_node_route_inf[node].occ()||bool(ledger_owners[size_t(query_net)].count(n))!=bool(connection_owned.count(n)))throw std::runtime_error("query shadow ledger mismatch");}
}
static void ledger_entry(const RouteTreeNode&,const ConnectionParameters& params){
 if(!std::getenv("ROUTECAST_QUERY_FILE"))return;
 std::set<size_t> actual;for(auto n:connection_owned)if(channel(n))actual.insert(n);
 if(actual!=ledger_owners[size_t(params.net_id_)])throw std::runtime_error("entry retained tree differs from update ledger");
 ledger_word(2);ledger_word(ledger_epoch);ledger_word(connection_id);ledger_word(size_t(params.net_id_));ledger_word(connection_pin);ledger_word(connection_sink);ledger_word(actual.size());for(auto n:actual)ledger_word(n);
}
static void ledger_boundary(int iteration){
 if(!std::getenv("ROUTECAST_QUERY_FILE"))return;if(connection_active)throw std::runtime_error("open connection at boundary");
 const auto& rr=g_vpr_ctx.device().rr_graph;for(auto node:rr.nodes())if(channel(size_t(node))&&ledger_counts[size_t(node)]!=g_vpr_ctx.routing().rr_node_route_inf[node].occ())throw std::runtime_error("boundary ledger mismatch");
 ledger_word(3);ledger_word(ledger_epoch);ledger_word(iteration);ledger_stream().flush();if(!ledger_stream())throw std::runtime_error("ledger write");
}
'''
 s+=helper;op=D/'observer.cpp';op.write_text(s);compile=p['compile'].copy();compile[compile.index('-c')+1]=str(op);compile[compile.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');link.insert(1,'-Wl,--wrap=_Z38pathfinder_update_cost_from_route_treeRK13RouteTreeNodei');paths=[Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',op,*[Path(x) for x in link if not x.startswith('-') and Path(x).is_file() and x!=str(D/'observer.o')]];bindings={str(x):sha(x) for x in paths};(D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Existing owned RAII connection object; wrap original tree occupancy update, forward once, reconstruct separate CHANNEL owner sets. Native routing costs untouched. Query payload summarized instead of repeated raw TSV; all observed CHANNEL queries assert ledger equality. Native parity pending.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',op,D/'observer.o']}),indent=2)+'\n')
if __name__=='__main__':main()
