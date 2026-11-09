"""Input-only six-word probability model; one post-ready iteration, no final-owner loader."""
import json,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'build/prince_input_mean_native_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);old=R/'build/prince_present_identity_v1_2026-10-20';p=json.loads((old/'protocol.json').read_text());s=(old/'observer.cpp').read_text();s=s.replace('static void consume_boundary(int);','static void consume_boundary(int);\nstatic void freeze_input_mean_ready(routecast_live::View&,int);');s=s.replace(' if(ready){',' if(ready){\n  freeze_input_mean_ready(view,iteration);',1)
 s=s.replace('static uint64_t identity_returns=0;','''static uint64_t identity_returns=0;
static uint64_t mean_ready_iteration=0,mean_window_calls=0,mean_eligible=0,mean_changed=0,mean_lowered=0,mean_identity_checked=0,mean_positive_delta=0;
static uint64_t mean_cells[4]={};
static int mean_mode=-1;
static float mean_base[2],mean_conditional[2][2];
static std::vector<uint32_t> mean_ready_codes;
static uint32_t mean_multi=0;
using MeanKey=std::array<uint64_t,6>;
using MeanWitness=std::array<uint64_t,18>;
static std::map<MeanKey,MeanWitness> mean_witnesses;
static void load_input_mean_model();
static void flush_mean_witnesses(int);
''')
 s=s.replace("<<identity_returns<<'\\n';if(!out)","<<identity_returns<<'\\t'<<mean_window_calls<<'\\t'<<mean_eligible<<'\\t'<<mean_changed<<'\\t'<<mean_lowered<<'\\t'<<mean_ready_iteration;for(auto n:mean_cells)out<<'\\t'<<n;out<<'\\t'<<mean_identity_checked<<'\\t'<<mean_positive_delta<<'\\n';if(!out)")
 s=s.replace('ledger_boundary(iteration);identity_returns=0;','flush_mean_witnesses(iteration);ledger_boundary(iteration);identity_returns=0;mean_window_calls=mean_eligible=mean_changed=mean_lowered=mean_identity_checked=mean_positive_delta=0;for(auto& n:mean_cells)n=0;')
 start=s.index('static float conditional_identity(RRNodeId node,float pres,float original){');s=s[:start]+'''
static float decoded(uint32_t word){float value;std::memcpy(&value,&word,4);return value;}
static void load_input_mean_model(){
 if(mean_mode!=-1)return;
 if(std::getenv("ROUTECAST_LABEL_OTHER_PAYLOAD")||std::getenv("ROUTECAST_LABEL_OTHER_ORACLE"))throw std::runtime_error("final-owner inputs forbidden for learned inference");
 const char* mode=std::getenv("ROUTECAST_INPUT_MEAN_MODE");if(!mode)throw std::runtime_error("mean mode required");std::string name(mode);if(name=="identity")mean_mode=0;else if(name=="base")mean_mode=1;else if(name=="ready")mean_mode=2;else if(name=="residual")mean_mode=3;else throw std::runtime_error("unknown input mean mode");
 const char* path=std::getenv("ROUTECAST_INPUT_MEAN_PAYLOAD");const char* expected=std::getenv("ROUTECAST_INPUT_MEAN_SHA256");if(!path||!expected)throw std::runtime_error("model payload required");auto begin=stamp();std::ifstream file(path);std::ostringstream body;body<<file.rdbuf();if(!file)throw std::runtime_error("mean payload read");std::string text=body.str();std::istringstream hashed(text);std::string digest=vtr::secure_digest_stream(hashed);if(digest!="SHA256:"+std::string(expected))throw std::runtime_error("mean payload digest mismatch");
 std::istringstream input(text);std::string marker;std::getline(input,marker);if(marker!="INPUT_ONLY_READY_MEAN_V1")throw std::runtime_error("mean model kind");std::vector<std::string> bound(6),identity(7);for(auto& x:bound)if(!std::getline(input,x))throw std::runtime_error("mean bound fields");std::ifstream ids(std::getenv("ROUTECAST_LIVE_IDENTITY"));for(auto& x:identity)if(!std::getline(ids,x))throw std::runtime_error("mean current identity");if(bound[0]!=identity[0]||bound[1]!=identity[1]||bound[2]!=identity[2]||bound[3]!=identity[5]||bound[4]!=identity[6]||bound[5]!=active_config)throw std::runtime_error("mean active identity mismatch");
 std::string models_hash,group;if(!std::getline(input,models_hash)||!std::getline(input,group)||models_hash.size()!=64||bound[3].substr(bound[3].find_last_of('/')+1)!=group)throw std::runtime_error("mean fold identity");uint64_t nets,nodes,training;if(!(input>>nets>>nodes>>training)||nets!=g_vpr_ctx.routing().route_trees.size()||nodes!=g_vpr_ctx.device().rr_graph.num_nodes()||training!=4)throw std::runtime_error("mean shape");std::set<std::string> seen;for(uint64_t i=0;i<training;++i){std::string name;if(!(input>>name)||!seen.insert(name).second||name.substr(name.find_last_of('/')+1)==group)throw std::runtime_error("same episode in model training");}
 for(int i=0;i<6;++i){uint64_t bits;if(!(input>>bits)||bits>UINT32_MAX)throw std::runtime_error("mean word");float value=decoded(uint32_t(bits));if(!std::isfinite(value)||value<0||value>1)throw std::runtime_error("mean probability domain");if(i<2)mean_base[i]=value;else mean_conditional[(i-2)/2][(i-2)%2]=value;}std::string extra;if(input>>extra)throw std::runtime_error("mean trailing input");auto end=stamp();const char* output=std::getenv("ROUTECAST_QUERY_FILE");if(output){std::ofstream receipt(std::string(output)+".model_load.tsv");receipt<<begin<<'\\t'<<end<<'\\t'<<digest.substr(7)<<'\\t'<<bound[3]<<'\\t'<<group<<'\\t'<<mean_mode<<'\\t'<<models_hash<<'\\n';if(!receipt)throw std::runtime_error("mean load receipt");}
}
static void freeze_input_mean_ready(routecast_live::View& view,int iteration){
 if(mean_ready_iteration||mean_mode<0)throw std::runtime_error("mean ready state");mean_ready_iteration=iteration;mean_ready_codes.assign(view.node_count(),0);mean_multi=uint32_t(view.net_count()+1);
 for(size_t i=0;i<view.net_count();++i){auto net=view.net(i);if(net.ignored)continue;for(auto node:view.owned_channels(net.endpoint)){auto& code=mean_ready_codes.at(node);uint32_t own=uint32_t(net.native+1);if(!code)code=own;else if(code!=own)code=mean_multi;}}
 for(size_t n=0;n<view.node_count();++n){auto rr=view.rr(n);if(rr.kind!=4&&rr.kind!=5)continue;if(rr.capacity!=1)throw std::runtime_error("mean unsupported capacity");uint32_t code=mean_ready_codes[n];if((rr.occupancy==0&&code!=0)||(rr.occupancy==1&&(code==0||code==mean_multi))||(rr.occupancy>1&&code!=mean_multi))throw std::runtime_error("mean ready owner coherence");}
 const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path){std::ofstream file(std::string(path)+".ready_codes.bin",std::ios::binary);file.write("RCMEAN01",8);put<uint64_t>(file,iteration);put<uint64_t>(file,view.node_count());put<uint64_t>(file,view.net_count());for(auto code:mean_ready_codes)put<uint32_t>(file,code);file.close();if(!file)throw std::runtime_error("mean ready codes write");}
}
static float conditional_identity(RRNodeId node,float pres,float original){
 if(!channel(size_t(node)))return original;const auto& d=g_vpr_ctx.device();const auto& rt=g_vpr_ctx.routing();if(d.rr_graph.node_capacity(node)!=1||rt.non_configurable_bitset.get(node))throw std::runtime_error("mean unsupported CHANNEL capacity/group");if(!connection_active||query_net<0)throw std::runtime_error("mean connection context");ledger_query(node);load_input_mean_model();int own=int(connection_owned.count(size_t(node)));int occ=rt.rr_node_route_inf[node].occ();if(occ<own)throw std::runtime_error("mean negative other demand");bool window=mean_ready_iteration>0&&uint64_t(phase_iteration)==mean_ready_iteration;bool eligible=window&&occ==own;int ready=0;float delta=0;
 if(window)++mean_window_calls;
 if(eligible){++mean_eligible;uint32_t code=mean_ready_codes.at(size_t(node));ready=code!=0&&(code==mean_multi||code!=uint32_t(query_net+1));++mean_cells[own*2+ready];if(mean_mode==1)delta=mean_base[own];else if(mean_mode==2)delta=mean_conditional[own][ready];else if(mean_mode==3)delta=std::max(0.f,mean_conditional[own][ready]-mean_base[own]);}
 float h=float(occ)+delta;float present=(1.+pres*h);auto index=d.rr_graph.node_cost_index(node);float replacement=d.rr_indexed_data[index].base_cost*rt.rr_node_route_inf[node].acc_cost*present;if(!std::isfinite(replacement)||replacement<original){++mean_lowered;throw std::runtime_error("mean lowered/invalid native cost");}if(delta==0){if(qbits(replacement)!=qbits(original))throw std::runtime_error("mean inactive identity mismatch");++mean_identity_checked;}else ++mean_positive_delta;if(qbits(replacement)!=qbits(original))++mean_changed;
 if(eligible){MeanKey key{{uint64_t(own),uint64_t(ready),qbits(pres),qbits(rt.rr_node_route_inf[node].acc_cost),qbits(d.rr_indexed_data[index].base_cost),uint64_t(mean_mode)}};MeanWitness value{{uint64_t(query_net),size_t(node),connection_id,uint64_t(occ),uint64_t(own),uint64_t(ready),qbits(pres),qbits(rt.rr_node_route_inf[node].acc_cost),qbits(d.rr_indexed_data[index].base_cost),qbits(mean_base[own]),qbits(mean_conditional[own][ready]),qbits(delta),qbits(h),qbits(original),qbits(replacement),uint64_t(mean_mode),1,ledger_epoch}};auto found=mean_witnesses.find(key);if(found==mean_witnesses.end())mean_witnesses.emplace(key,value);else{for(size_t i=3;i<16;++i)if(found->second[i]!=value[i])throw std::runtime_error("mean witness grouping mismatch");++found->second[16];}}
 ++identity_returns;return replacement;
}
static void flush_mean_witnesses(int iteration){const char* path=std::getenv("ROUTECAST_QUERY_FILE");if(path&&!mean_witnesses.empty()){std::ofstream f(std::string(path)+".mean_witness.tsv",std::ios::app);for(const auto& item:mean_witnesses){f<<iteration;for(auto x:item.second)f<<'\\t'<<x;f<<'\\n';}if(!f)throw std::runtime_error("mean witnesses write");}mean_witnesses.clear();}
'''
 assert 'final_owner_codes' not in s and 'load_label_oracle' not in s;op=D/'observer.cpp';op.write_text(s);compile=p['compile'].copy();compile[compile.index('-c')+1]=str(op);compile[compile.index('-o')+1]=str(D/'observer.o');link=p['link'].copy();link=[str(D/'observer.o') if x==str(old/'observer.o') else x for x in link];link[link.index('-o')+1]=str(D/'vpr');paths=[Path(__file__),old/'protocol.json',old/'receipt.json',old/'observer.cpp',op,R/'experiments/prince_sparse_other_mean_calibration_v1_2026-10-20/native_mean_component_trial_design_v1.json',*[Path(x) for x in link if not x.startswith('-') and Path(x).is_file() and x!=str(D/'observer.o')]];bindings={str(x):sha(x) for x in paths};(D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Input-only six probability words and live ready snapshot. Identity/base/ready/residual modes, first post-ready iteration only. No final owner loader; final-owner env inputs forbidden. Six-field payload/current-profile and episode exclusion checks, scalar witness coverage, non-suppression and inactive bit-identity guards. No prediction-quality/fullpaid claim.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  print(name,code,flush=True)
  if code:raise SystemExit(code)
 assert all(sha(x)==h for x,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(D/'vpr'),bindings={str(x):sha(x) for x in [D/'protocol.json',op,D/'observer.o']}),indent=2)+'\n')
if __name__=='__main__':main()
