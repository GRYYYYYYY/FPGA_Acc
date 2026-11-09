"""Supplementary per-call raw query capture; bounded active-prefix validation only."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'build/prince_cost_advance_ablation_v1_2026-10-20';D=R/'build/prince_cost_raw_prefix_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);p=json.loads((O/'protocol.json').read_text());s=(O/'observer.cpp').read_text();s=s.replace('static int cost_ready_iteration=0;','static std::string cost_raw_query_bytes;\nstatic void cost_raw_flush(int);\nstatic void cost_raw_maybe_stop(int);\nstatic int cost_ready_iteration=0;',1);needle=' ledger_query(node);++query_calls;';assert s.count(needle)==1;s=s.replace(needle,' cost_raw_query_bytes.append(reinterpret_cast<const char*>(key.data()),sizeof(key));\n'+needle);needle='static void flush_queries(int iteration){';assert s.count(needle)==1;s=s.replace(needle,needle+'\n cost_raw_flush(iteration);');needle=' consume_boundary(i);';assert s.count(needle)==1;s=s.replace(needle,needle+'cost_raw_maybe_stop(i);')
 s+='''
static void cost_raw_flush(int iteration){
 const char* directory=std::getenv("ROUTECAST_RAW_QUERY_DIR");if(!directory)throw std::runtime_error("raw query directory missing");if(cost_raw_query_bytes.size()!=query_calls*15*sizeof(uint64_t))throw std::runtime_error("raw query count");
 std::string path=std::string(directory)+"/phase_"+std::to_string(iteration)+".bin";std::ofstream f(path,std::ios::binary);f.write(cost_raw_query_bytes.data(),cost_raw_query_bytes.size());f.close();if(!f)throw std::runtime_error("raw query write");std::istringstream input(cost_raw_query_bytes);auto digest=vtr::secure_digest_stream(input);std::ofstream meta(std::string(std::getenv("ROUTECAST_QUERY_FILE"))+".raw_sha.tsv",std::ios::app);meta<<iteration<<'\\t'<<query_calls<<'\\t'<<cost_raw_query_bytes.size()<<'\\t'<<digest<<'\\n';if(!meta)throw std::runtime_error("raw query digest");cost_raw_query_bytes.clear();
}
static void cost_raw_maybe_stop(int iteration){
 if(cost_ready_iteration&&iteration==cost_ready_iteration+1){std::ofstream f(std::string(std::getenv("ROUTECAST_QUERY_FILE"))+".intentional_prefix_stop.tsv");f<<"INTENTIONAL_QUERY_PREFIX_VALIDATION_NOT_ROUTING_SUCCESS\\t"<<iteration<<'\\t'<<cost_ready_iteration<<'\\n';f.close();if(!f)throw std::runtime_error("prefix stop marker");std::fflush(nullptr);std::_Exit(0);}
}
'''
 op=D/'observer.cpp';op.write_text(s);cc=p['compile'].copy();cc[cc.index('-c')+1]=str(op);cc[cc.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(O/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');design=R/'experiments/prince_cost_advance_ablation_trial_v1_2026-10-20/raw_query_prefix_validation_design_v1.json';bindings={str(x):sha(x) for x in [Path(__file__),O/'protocol.json',O/'receipt.json',O/'observer.cpp',op,design,*[Path(x) for x in link if x.endswith('/libvpr.a')]]};(D/'protocol.json').write_text(json.dumps(dict(compile=cc,link=link,bindings=bindings,scope='Raw observed QueryKey bytes in order,per phase. Original cost function values/args unchanged. Intentional ready+1 prefix stop is supplemental validation,not native legal success. Existing owned route archive reused immutable.'),indent=2)+'\n')
 for name,cmd in [('compile',cc),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',op,D/'observer.o']}),indent=2)+'\n')
if __name__=='__main__':main()
