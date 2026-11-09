"""Frozen post-ready pres/global-acc component interventions in owned native copies."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_cost_advance_ablation_v1_2026-10-20';OLD=R/'build/prince_ownership_ledger_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);p=json.loads((OLD/'protocol.json').read_text());s=(OLD/'route.cpp').read_text();decl='extern "C" float routecast_cost_acc_factor(int,float);\nextern "C" float routecast_cost_pres_step(int,float,float);\n';needle='extern "C" void routecast_restore_tree(const RouteTreeNode&,int,size_t);';assert s.count(needle)==1;s=s.replace(needle,decl+needle)
 replacements={'pathfinder_update_acc_cost_and_overuse_info(0., overuse_info);':'pathfinder_update_acc_cost_and_overuse_info(routecast_cost_acc_factor(itry,0.f), overuse_info);','pathfinder_update_acc_cost_and_overuse_info(router_opts.acc_fac, overuse_info);':'pathfinder_update_acc_cost_and_overuse_info(routecast_cost_acc_factor(itry,router_opts.acc_fac), overuse_info);','pres_fac *= router_opts.pres_fac_mult;':'pres_fac = routecast_cost_pres_step(itry,pres_fac,router_opts.pres_fac_mult);'}
 for old,new in replacements.items():assert s.count(old)==1;s=s.replace(old,new)
 rp=D/'route.cpp';rp.write_text(s);restored=s.replace(decl,'')
 for old,new in replacements.items():restored=restored.replace(new,old)
 assert restored==(OLD/'route.cpp').read_text();observer=(OLD/'observer.cpp').read_text();observer=observer.replace('static int phase_iteration=0;','static int cost_ready_iteration=0;\nstatic int phase_iteration=0;',1);needle=' if(ready){';assert observer.count(needle)==1;observer=observer.replace(needle,needle+'\n  if(cost_ready_iteration)throw std::runtime_error("duplicate cost policy ready");cost_ready_iteration=iteration;',1)
 observer+='''
static int cost_policy_mode(){
 static int mode=[](){
  const char* env=std::getenv("ROUTECAST_COST_MODE");const char* path=std::getenv("ROUTECAST_COST_POLICY_FILE");if(!env||!path)throw std::runtime_error("missing cost policy");std::string name(env);int value=name=="native"?0:name=="hold_pres"?1:name=="hold_acc"?2:name=="hold_both"?3:-1;if(value<0)throw std::runtime_error("unknown cost policy");
  std::ifstream f(path);std::vector<std::string> lines;std::string line;while(std::getline(f,line))lines.push_back(line);std::ifstream g(std::getenv("ROUTECAST_LIVE_IDENTITY"));std::vector<std::string> id;while(std::getline(g,line))id.push_back(line);if(lines.size()!=5||id.size()!=7||lines[0]!="COST_ADVANCE_ABLATION_V1"||lines[1]!=name||lines[2]!=id[5]||lines[3]!=id[3]||lines[4]!=id[6])throw std::runtime_error("cost policy identity mismatch");
  std::ofstream log(std::string(std::getenv("ROUTECAST_QUERY_FILE"))+".cost_policy_load.tsv");log<<value<<'\\t'<<name<<'\\t'<<id[5]<<'\\t'<<id[3]<<'\\t'<<id[6]<<'\\t'<<active_config<<'\\n';if(!log)throw std::runtime_error("cost policy load log");return value;
 }();return mode;
}
static void cost_advance_log(int tag,int iteration,int mode,float a,float b,float effective){
 const char* p=std::getenv("ROUTECAST_QUERY_FILE");if(!p)throw std::runtime_error("cost policy requires ledger");std::ofstream f(std::string(p)+".cost_advances.tsv",std::ios::app);f<<tag<<'\\t'<<iteration<<'\\t'<<cost_ready_iteration<<'\\t'<<mode<<'\\t'<<qbits(a)<<'\\t'<<qbits(b)<<'\\t'<<qbits(effective)<<'\\t'<<(cost_ready_iteration!=0)<<'\\t'<<ledger_epoch<<'\\t'<<phase_iteration<<'\\n';if(!f)throw std::runtime_error("cost advance log");
}
extern "C" float routecast_cost_acc_factor(int iteration,float original){int mode=cost_policy_mode();float effective=cost_ready_iteration&&(mode&2)?0.f:original;cost_advance_log(1,iteration,mode,original,0.f,effective);return effective;}
extern "C" float routecast_cost_pres_step(int iteration,float previous,float multiplier){int mode=cost_policy_mode();float effective=cost_ready_iteration&&(mode&1)?previous:previous*multiplier;cost_advance_log(2,iteration,mode,previous,multiplier,effective);return effective;}
'''
 op=D/'observer.cpp';op.write_text(observer);oc=p['compile'].copy();oc[oc.index('-c')+1]=str(op);oc[oc.index('-o')+1]=str(D/'observer.o');cc=p['route_compile'].copy();cc[cc.index('-c')+1]=str(rp);cc[cc.index('-o')+1]=str(D/'route.cpp.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(OLD/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');archive=next(Path(x) for x in link if x.endswith('/libvpr.a'));owned=D/'libvpr.a';shutil.copyfile(archive,owned);link=[str(owned) if x==str(archive) else x for x in link];design=R/'experiments/prince_attempt_scope_competition_v1_2026-10-20/post_ready_cost_advance_ablation_design_v1.json';bindings={str(x):sha(x) for x in [Path(__file__),OLD/'protocol.json',OLD/'receipt.json',OLD/'route.cpp',OLD/'observer.cpp',archive,rp,op,design]};(D/'protocol.json').write_text(json.dumps(dict(compile=oc,route_compile=cc,link=link,bindings=bindings,scope='Three explicit callsite replacements only:two global acc arguments and pres multiplier. Locally reserved OPIN behavior unchanged. Mode bound to native graph/net/place/binary/case/launcher identity via policy payload;real ready trigger only. No learned/future labels or forecast.',advance_schema=['tag1_acc_or2_pres','iteration','ready_iteration0_if_unarmed','mode_bitmask','original_argument_or_previous_pres_bits','multiplier_or0_bits','effective_factor_or_next_uncapped_pres_bits','armed','ledger_epoch','observed_phase_iteration']),indent=2)+'\n')
 for name,cmd in [('route_compile',cc),('observer_compile',oc),('archive_replace',['ar','r',str(owned),str(D/'route.cpp.o')]),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',owned,op,rp,D/'observer.o',D/'route.cpp.o']}),indent=2)+'\n')
if __name__=='__main__':main()
