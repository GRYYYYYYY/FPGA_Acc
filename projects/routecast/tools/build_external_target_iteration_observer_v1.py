"""Isolated external seed LOOKAHEAD policy ablation; preserves retained/nonlookahead."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19'
D=R/'build/native_external_target_iteration_observer_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text());receipt=json.loads((B/'receipt.json').read_text())
 assert sha(receipt['binary'])==receipt['binary_sha256']
 assert all(sha(k)==v for k,v in p['bindings'].items())
 D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source')
 f=D/'source/route.cpp';s=f.read_text()
 A=R/'experiments/prospective_external_family_final_critical_path_attribution_v1_2026-10-19';C=R/'experiments/prospective_external_family_seed_retention_delay_diagnosis_v1_2026-10-19'
 targets=set();target_bindings={}
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';pp=A/case/'seed/worst_path_points.json';cp=C/case/'connections.json';target_bindings[str(pp)]=sha(pp);target_bindings[str(cp)]=sha(cp);cohort={r['connection_id']:r for r in json.loads(cp.read_text())}
  for row in json.loads(pp.read_text()):
   if row['classification']=='EXTERNAL_NATIVE_CID':
    for cid in row['CID_candidates']:
     r=cohort[cid];targets.add((r['native_net_id'],r['local_pin']))
 initializer=','.join('{'+str(n)+','+str(pin)+'}' for n,pin in sorted(targets))
 code=r'''
        auto observe_targets = [&](const char* phase) {
            FILE* out=std::fopen("target_iterations.tsv",itry==1 && phase[0]=='B'?"wx":"a");
            if(!out)throw std::runtime_error("target observer open");
            if(itry==1 && phase[0]=='B')std::fprintf(out,"phase\titeration\tpres_fac\tnet\tname\tpin\tdelay_s\tcriticality\tpath_sink_to_source_node_switch_occ_hist_pres\n");
            const std::pair<size_t,size_t> targets[]={TARGETS};
            for(const auto& target:targets) {
                ParentNetId net(target.first);size_t pin=target.second;
                if(pin>=net_list.net_pins(net).size())throw std::runtime_error("target pin range");
                float crit=calculate_clb_net_pin_criticality(*timing_info,netlist_pin_lookup,net_list.net_pin(net,pin),is_flat);
                std::fprintf(out,"%s\t%d\t%.9g\t%zu\t%s\t%zu\t%.9g\t%.9g\t",phase,itry,double(pres_fac),target.first,net_list.net_name(net).c_str(),pin,double(net_delay[net][pin]),double(crit));
                if(route_ctx.route_trees[net]) {
                    auto sink=route_ctx.route_trees[net]->find_by_isink(pin);
                    if(sink) {
                        const RouteTreeNode* node=&sink.value();
                        while(node) {
                            auto rr=node->inode;
                            std::fprintf(out,"%zu:%zu:%d:%.9g:%.9g,",size_t(rr),size_t(node->parent_switch),route_ctx.rr_node_route_inf[rr].occ(),double(route_ctx.rr_node_route_inf[rr].acc_cost),double(get_single_rr_cong_pres_cost(rr,pres_fac)));
                            auto parent=node->parent();node=parent?&parent.value():nullptr;
                        }
                    }
                }
                std::fputc('\n',out);
            }
            if(std::fclose(out))throw std::runtime_error("target observer close");
        };
        observe_targets("BEFORE");
'''.replace('TARGETS',initializer)
 anchor='        RouteIterResults iter_results = netlist_router->route_netlist(itry, pres_fac, worst_negative_slack);';assert s.count(anchor)==1;s=s.replace(anchor,code+anchor)
 anchor="        timing_info->set_warn_unconstrained(false); //Don't warn again about unconstrained nodes again during routing";assert s.count(anchor)==1;s=s.replace(anchor,anchor+'\n        observe_targets("AFTER");');f.write_text(s)

 compile=[x.replace(str(B),str(D)) for x in p['compile']];link=[x.replace(str(B),str(D)) for x in p['link']]
 bindings={**target_bindings,str(B/'protocol.json'):sha(B/'protocol.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for f in (D/'source').rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 protocol=dict(compile=compile,link=link,bindings=bindings,policy='Read-only target snapshots BEFORE invocation and AFTER normal post-route STA, all3 union external points from seeded worst paths; posthoc diagnostics only, no policy selection. External seed under LOOKAHEAD retains lookahead delays before initial STA. Same-process retained_input and nonlookahead seed delays unchanged. After first routable iteration restore ALL nonignored tree pin Tdel; clear delay cache and invalidate all timing edges before normal post-route STA. Native checks retained. Trees/occupancy retained. Observer initial perpin and first iteration outputs unchanged.',scope='All3 fixed cold/seed native-only pilot. Full physical/canonical,15616 required CIDs,CPD and wirelength nonregress. No percase selection or full paid timing acceptance. Cold equivalence and initial cold/seed perpin equality pending.')
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==v for k,v in bindings.items())
 (D/'receipt.json').write_text(json.dumps(dict(status='BUILT_RUNTIME_VERIFICATION_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT_RUNTIME_VERIFICATION_PENDING',flush=True)
if __name__=='__main__':main()
