"""Private first-iteration hint expiry with bit-exact guard and state dumps."""
import pathlib,json,hashlib,shutil,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 B=R/'build/native_excess_preload_state_v2_2026-10-19';P=R/'experiments/mmc_first_iteration_forecast_hint_protocol_v1_2026-10-19/protocol.json';plan=json.loads(P.read_text());receipt=json.loads((B/'receipt.json').read_text())
 for doc in [plan,receipt]:
  for p,h in doc['bindings'].items():assert sha(pathlib.Path(p))==h
 assert sha(B/'sequence_vpr')==receipt['binary_sha256'];D=R/'build/native_first_iteration_hint_v1_2026-10-19';D.mkdir(exist_ok=False);S=D/'source';S.mkdir()
 for p in (B/'source').glob('*.h'):shutil.copyfile(p,S/p.name)
 original=(B/'source/route.cpp').read_text();anchor='    if(const char* preload=std::getenv("ROUTECAST_EXCESS_PRELOAD")) {'
 declaration='''    const char* rc_hint_flag=std::getenv("ROUTECAST_FIRST_ITERATION_HINT");
    if(rc_hint_flag && (std::string(rc_hint_flag)!="1" || !std::getenv("ROUTECAST_EXCESS_PRELOAD")))
        throw std::runtime_error("first-iteration hint requires flag1 and explicit preload");
    const bool rc_expire_first_hint=rc_hint_flag!=nullptr;
    std::vector<std::pair<RRNodeId,float>> rc_first_hint_entries;
'''
 remember='        if(rc_expire_first_hint)rc_first_hint_entries=updates;\n'
 assignment='        for(const auto& update:updates)route_ctx.rr_node_route_inf[update.first].acc_cost=update.second;\n'
 point='        wirelength_info = calculate_wirelength_info(net_list, available_wirelength);'
 expiry='''        if(rc_expire_first_hint && itry==1) {
            // Native iteration1 has acc_fac0. Never erase unexpected measured history.
            for(const auto& entry:rc_first_hint_entries) {
                float current=route_ctx.rr_node_route_inf[entry.first].acc_cost;
                uint32_t observed,expected;
                std::memcpy(&observed,&current,sizeof(observed));
                std::memcpy(&expected,&entry.second,sizeof(expected));
                if(observed!=expected)throw std::runtime_error("hint expiry would erase unexpected native history");
            }
            const char* before=std::getenv("ROUTECAST_HINT_EXPIRY_BEFORE_DUMP");
            const char* after=std::getenv("ROUTECAST_HINT_EXPIRY_AFTER_DUMP");
            if(bool(before)!=bool(after))throw std::runtime_error("hint expiry snapshots require both paths");
            auto dump_costs=[&](const char* path) {
                if(!path)return;
                FILE* fp=std::fopen(path,"wbx");
                if(!fp)throw std::runtime_error("hint expiry snapshot exclusive open failed");
                std::fprintf(fp,"RCACCBITS1 %zu\\n",device_ctx.rr_graph.num_nodes());
                bool failed=false;
                for(size_t i=0;i<device_ctx.rr_graph.num_nodes();++i) {
                    float value=route_ctx.rr_node_route_inf[RRNodeId(i)].acc_cost;
                    uint32_t bits;std::memcpy(&bits,&value,sizeof(bits));
                    if(std::fwrite(&bits,sizeof(bits),1,fp)!=1)failed=true;
                }
                failed=failed||std::ferror(fp);int closed=std::fclose(fp);
                if(failed||closed)throw std::runtime_error("hint expiry snapshot write failed");
            };
            dump_costs(before);
            for(const auto& entry:rc_first_hint_entries)route_ctx.rr_node_route_inf[entry.first].acc_cost=1.f;
            dump_costs(after);
            VTR_LOG("ROUTECAST first iteration hint expired entries=%zu\\n",rc_first_hint_entries.size());
        }
'''
 assert original.count(anchor)==original.count(assignment)==original.count(point)==1
 text=original.replace(anchor,declaration+anchor).replace(assignment,assignment+remember).replace(point,expiry+point)
 recovered=text.replace(declaration,'').replace(remember,'').replace(expiry,'');assert recovered==original
 (S/'route.cpp').write_text(text);shutil.copyfile(__file__,S/'build.py');old=json.loads((B/'protocol.json').read_text());compile=[str(S/'route.cpp') if x==str(B/'source/route.cpp') else str(D/'route.o') if x==str(B/'route.o') else x for x in old['compile']];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in old['link']];bindings={str(p):sha(p) for p in [P,B/'receipt.json',B/'source/route.cpp',pathlib.Path(__file__).resolve(),*S.iterdir()]}
 (D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,link=link,strip_additions_recovers_bound_base_source_exactly=True,expiry_boundary='After native iteration1 acc_fac0 update, before wirelength/STA summary and iteration2; only initial hint CHAN entries restored after bit guards.'),indent=2)+'\n')
 print('FIRST_ITERATION_HINT_COMPILE_START',flush=True)
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(pathlib.Path(p))==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status='PRIVATE_FIRST_ITERATION_HINT_BUILD_PASS_RUNTIME_ADMISSION_PENDING',bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),strip_additions_recovers_bound_base_source_exactly=True,semantic_runtime_admitted=False,native_utility_proven=False),indent=2)+'\n');print('FIRST_ITERATION_HINT_BUILD_PASS',flush=True)
if __name__=='__main__':main()
