"""Presearch native timing graph/atom map only; dynamic criticality model not implemented."""
import json,hashlib,shutil,subprocess,os,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19';N=R/'build/native_external_shared_sink_native_v1_2026-10-19';D=R/'build/native_external_delay_components_v1_2026-10-19';O=E/'prospective_external_family_delay_components_v1_2026-10-19';BASE=E/'prospective_external_family_native_shared_sink_native_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 b=read(N/'receipt.json');assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());D.mkdir(exist_ok=False);O.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/route.cpp';s=f.read_text();s='#include "VprTimingGraphResolver.h"\n#include "atom_lookup.h"\n#include "clustered_netlist_utils.h"\n#include "tatum/TimingConstraints.hpp"\n'+s
 anchor='    std::unique_ptr<NetPinTimingInvalidator> pin_timing_invalidator;';assert s.count(anchor)==1
 code=r'''
    {


        auto dump_components=[&](const char* name) {
            const auto& tg=*g_vpr_ctx.timing().graph;
            VprTimingGraphResolver resolver(atom_ctx.nlist,atom_ctx.lookup,tg,*delay_calc,is_flat,g_vpr_ctx.placement().blk_loc_registry());
            resolver.set_detail_level(e_timing_report_detail::AGGREGATED);
            FILE* f=std::fopen(name,"wx");if(!f)throw std::runtime_error("components open");
            std::fprintf(f,"edge\tmode\tcomponent\ttype\tdelay_s\n");
            for(auto edge:tg.edges())if(tg.edge_type(edge)==tatum::EdgeType::INTERCONNECT) {
                for(auto mode:{tatum::DelayType::MAX,tatum::DelayType::MIN}) {
                    auto breakdown=resolver.edge_delay_breakdown(edge,mode);size_t index=0;
                    for(const auto& c:breakdown.components)std::fprintf(f,"%zu\t%s\t%zu\t%s\t%.9g\n",size_t(edge),mode==tatum::DelayType::MAX?"MAX":"MIN",index++,c.type_name.c_str(),double(float(c.delay)));
                }
            }
            if(std::fclose(f))throw std::runtime_error("components close");
        };
        dump_components("components_before.tsv");
        const char* perturbation=std::getenv("ROUTECAST_TIMING_PERTURBATION");
        if(!perturbation)throw std::runtime_error("explicit perturbation required");
        std::string mode(perturbation);if(mode!="scaled" && mode!="sparse_plus" && mode!="sparse_zero")throw std::runtime_error("unknown perturbation");
        FILE* changes=std::fopen("delay_changes.tsv","wx");if(!changes)throw std::runtime_error("changes open");
        std::fprintf(changes,"net\tpin\tbefore_s\tafter_s\n");
        for(auto net:net_list.nets())if(!net_list.net_is_ignored(net))for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
            float old=net_delay[net][pin],value=old;
            if(mode=="scaled")value=old*1.25f;
            if(mode=="sparse_plus" && size_t(net)%17==0)value=old+0.25e-9f;
            if(mode=="sparse_zero" && size_t(net)%29==0)value=0.f;
            net_delay[net][pin]=value;
            std::fprintf(changes,"%zu\t%zu\t%.9g\t%.9g\n",size_t(net),pin,double(old),double(value));
        }
        if(std::fclose(changes))throw std::runtime_error("changes close");
        delay_calc->clear_cache();
        for(auto edge:g_vpr_ctx.timing().graph->edges())timing_info->invalidate_delay(edge);
        timing_info->update();
        dump_components("components_after.tsv");
        FILE* updated=std::fopen("updated_connections.tsv","wx");if(!updated)throw std::runtime_error("updated open");
        std::fprintf(updated,"net\tpin\tsource_rr\tsink_rr\tdelay_s\tcriticality\tslack_s\n");
        for(auto net:net_list.nets())if(!net_list.net_is_ignored(net))for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
            auto p=net_list.net_pin(net,pin);
            float crit=calculate_clb_net_pin_criticality(*timing_info,netlist_pin_lookup,p,is_flat);
            float slack=calculate_clb_net_pin_setup_slack(*timing_info,netlist_pin_lookup,ClusterPinId(size_t(p)));
            std::fprintf(updated,"%zu\t%zu\t%zu\t%zu\t%.9g\t%.9g\t%.9g\n",size_t(net),pin,size_t(route_ctx.net_rr_terminals[net][0]),size_t(route_ctx.net_rr_terminals[net][pin]),double(net_delay[net][pin]),double(crit),double(slack));
        }
        if(std::fclose(updated))throw std::runtime_error("updated close");
        const auto& graph=*g_vpr_ctx.timing().graph;
        FILE* nodes=std::fopen("timing_nodes.tsv","wx");FILE* edges=std::fopen("timing_edges.tsv","wx");FILE* atoms=std::fopen("timing_atoms.tsv","wx");
        if(!nodes || !edges || !atoms)throw std::runtime_error("timing graph output open");
        std::fprintf(nodes,"node\ttype\n");std::fprintf(edges,"edge\tsource\tsink\ttype\tdisabled\tvalue_max_or_setup_s\tvalue_min_or_hold_s\n");
        for(auto node:graph.nodes())std::fprintf(nodes,"%zu\t%d\n",size_t(node),int(graph.node_type(node)));
        for(auto edge:graph.edges()) {
            bool capture=graph.edge_type(edge)==tatum::EdgeType::PRIMITIVE_CLOCK_CAPTURE;
            float maxvalue=capture?float(delay_calc->setup_time(graph,edge)):float(delay_calc->max_edge_delay(graph,edge));
            float minvalue=capture?float(delay_calc->hold_time(graph,edge)):float(delay_calc->min_edge_delay(graph,edge));
            std::fprintf(edges,"%zu\t%zu\t%zu\t%d\t%d\t%.9g\t%.9g\n",size_t(edge),size_t(graph.edge_src_node(edge)),size_t(graph.edge_sink_node(edge)),int(graph.edge_type(edge)),int(graph.edge_disabled(edge)),double(maxvalue),double(minvalue));
        }
        std::fprintf(atoms,"atom_pin\tatom\tport\tbit\texternal_node\tinternal_node\tnative_net\tlocal_pin\traw_criticality\tsetup_slack_s\n");
        for(auto pin:atom_ctx.nlist.pins()) {
            auto block=atom_ctx.nlist.pin_block(pin);auto ex=atom_ctx.lookup.atom_pin_tnode(pin,BlockTnode::EXTERNAL);auto in=atom_ctx.lookup.atom_pin_tnode(pin,BlockTnode::INTERNAL);auto cp=netlist_pin_lookup.connected_clb_pin(pin);
            std::fprintf(atoms,"%zu\t%s\t%s\t%d\t",size_t(pin),atom_ctx.nlist.block_name(block).c_str(),atom_ctx.nlist.port_name(atom_ctx.nlist.pin_port(pin)).c_str(),atom_ctx.nlist.pin_port_bit(pin));
            if(ex)std::fprintf(atoms,"%zu",size_t(ex));std::fputc('\t',atoms);if(in)std::fprintf(atoms,"%zu",size_t(in));std::fputc('\t',atoms);
            bool data=false;
            if(cp) {auto net=cluster_ctx.clb_nlist.pin_net(cp);int local=cluster_ctx.clb_nlist.pin_net_index(cp);std::fprintf(atoms,"%zu\t%d\t",size_t(net),local);data=local>0 && !cluster_ctx.clb_nlist.net_is_ignored(net);}
            else std::fprintf(atoms,"\t\t");
            if(data)std::fprintf(atoms,"%.9g\t%.9g",double(timing_info->setup_pin_criticality(pin)),double(timing_info->setup_pin_slack(pin)));
            else std::fprintf(atoms,"\t");std::fputc('\n',atoms);
        }
        if(std::fclose(nodes) || std::fclose(edges) || std::fclose(atoms))throw std::runtime_error("timing graph close");

        const auto& constraints=*timing_info->timing_constraints();
        FILE* cf=std::fopen("clock_constraints.tsv","wx");if(!cf)throw std::runtime_error("clock constraint open");
        auto id=[](auto value)->long long {return value?static_cast<long long>(size_t(value)):-1;};
        std::fprintf(cf,"H\t1\n");
        for(auto domain:constraints.clock_domains())std::fprintf(cf,"D\t%lld\t%lld\t%d\t%s\n",id(domain),id(constraints.clock_domain_source_node(domain)),int(constraints.is_virtual_clock(domain)),constraints.clock_domain_name(domain).c_str());
        for(auto kv:constraints.setup_constraints())std::fprintf(cf,"C\tSETUP\t%lld\t%lld\t%lld\t%.9g\n",id(kv.first.domain_pair.src_domain_id),id(kv.first.domain_pair.sink_domain_id),id(kv.first.capture_node),double(float(kv.second)));
        for(auto kv:constraints.hold_constraints())std::fprintf(cf,"C\tHOLD\t%lld\t%lld\t%lld\t%.9g\n",id(kv.first.domain_pair.src_domain_id),id(kv.first.domain_pair.sink_domain_id),id(kv.first.capture_node),double(float(kv.second)));
        for(auto delay:{tatum::DelayType::MAX,tatum::DelayType::MIN}) {
            const char* name=delay==tatum::DelayType::MAX?"MAX":"MIN";
            for(auto kv:constraints.input_constraints(delay))std::fprintf(cf,"I\t%s\t%lld\t%lld\t%.9g\n",name,id(kv.first),id(kv.second.domain),double(float(kv.second.constraint)));
            for(auto kv:constraints.output_constraints(delay))std::fprintf(cf,"O\t%s\t%lld\t%lld\t%.9g\n",name,id(kv.first),id(kv.second.domain),double(float(kv.second.constraint)));
        }
        for(auto kv:constraints.setup_clock_uncertainties())std::fprintf(cf,"U\tSETUP\t%lld\t%lld\t%.9g\n",id(kv.first.src_domain_id),id(kv.first.sink_domain_id),double(float(kv.second)));
        for(auto kv:constraints.hold_clock_uncertainties())std::fprintf(cf,"U\tHOLD\t%lld\t%lld\t%.9g\n",id(kv.first.src_domain_id),id(kv.first.sink_domain_id),double(float(kv.second)));
        for(auto arrival:{tatum::ArrivalType::EARLY,tatum::ArrivalType::LATE}) {
            const char* name=arrival==tatum::ArrivalType::EARLY?"EARLY":"LATE";
            for(auto kv:constraints.source_latencies(arrival))std::fprintf(cf,"L\t%s\t%lld\t%.9g\n",name,id(kv.first),double(float(kv.second)));
            for(auto domain:constraints.clock_domains())std::fprintf(cf,"QL\t%s\t%lld\t%.9g\n",name,id(domain),double(float(constraints.source_latency(domain,arrival))));
        }
        for(auto node:constraints.constant_generators())std::fprintf(cf,"G\t%lld\n",id(node));
        for(auto src:constraints.clock_domains())for(auto sink:constraints.clock_domains()) {
            std::fprintf(cf,"QU\t%lld\t%lld\t%.9g\t%.9g\n",id(src),id(sink),double(float(constraints.setup_clock_uncertainty(src,sink))),double(float(constraints.hold_clock_uncertainty(src,sink))));
            auto capture=[&](tatum::NodeId node) {std::fprintf(cf,"Q\t%lld\t%lld\t%lld\t%d\t%.9g\t%.9g\n",id(src),id(sink),id(node),int(constraints.should_analyze(src,sink,node)),double(float(constraints.setup_constraint(src,sink,node))),double(float(constraints.hold_constraint(src,sink,node))));};
            capture(tatum::NodeId::INVALID());
            for(auto node:graph.nodes())if(graph.node_type(node)==tatum::NodeType::SINK)capture(node);
        }
        if(std::fclose(cf))throw std::runtime_error("clock constraint close");
        timing_info->timing_constraints()->print_constraints();
        VTR_LOG("RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING\n");std::fflush(nullptr);std::exit(0);
    }
'''
 f.write_text(s.replace(anchor,code+anchor));p=read(B/'protocol.json');compile=[x.replace(str(B),str(D)) for x in p['compile']];link=read(N/'protocol.json')['link'];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(N/'sequence_vpr') else x for x in link];bindings={str(N/'receipt.json'):sha(N/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for path in (D/'source').rglob('*'):
  if path.is_file():bindings[str(path)]=sha(path)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Current nominal packed mapping after initial native STA only; export typed graph/capture setup-hold values, atom pin mappings and data sink criticalities. Exit before search. Native constraint ranges and resolved default/each-sink setup-hold getters exported; raw log retained. No dynamic timing model claimed.'),indent=2)+'\n')
 for stage,cmd in [('compile',compile),('link',link)]:
  with (D/(stage+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 basecases=[c for c in read(BASE/'manifest.json')['cases'] if c['case'].endswith('/cold')];cases=[dict(c,base_case=c['case'].removesuffix('/cold'),perturbation=mode,case=c['case']+'/'+mode) for c in basecases for mode in ('scaled','sparse_plus','sparse_zero')];(O/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,scope='Fixed all3 x scaled1.25/sparse NETmod17 add0.25ns/sparse NETmod29 zero, all data pins logged. Nominal packed mapping unchanged; synthetic delays not physical RR routes. initial_connections before perturbation retained; updated_connections authoritative after native cache clear/invalidation/STA. Public aggregated VprTimingGraphResolver component exports before/after only, no private header or source edits. Require original nine snapshot outputs unchanged and separate float32(driver+RR)+sink reconstruction. No quality/general STA acceptance.'),indent=2)+'\n')
 def run(c):
  case=c['base_case']+'/'+c['perturbation'];out=O/case;out.mkdir(parents=True)
  for k,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(c['inputs'][k],out/name)
  cmd=c['command'].copy();cmd[0]=str(D/'sequence_vpr');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
  env['ROUTECAST_TIMING_PERTURBATION']=c['perturbation']
  with (out/'native.log').open('x') as log:code=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  same=(out/'initial_connections.tsv').exists() and sha(out/'initial_connections.tsv')==sha(BASE/c['base_case']/'cold/native/initial_connections.tsv');row=dict(case=case,exit_code=code,no_route_generated=not list(out.glob('*.route')),initial_connection_bytes_equal=same,marker='RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING' in (out/'native.log').read_text());print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(O/'terminal.json').write_text(json.dumps(dict(status='ALL9_PUBLIC_COMPONENT_EXPORT_PERTURBATION_PROCESSES_TERMINAL',rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
