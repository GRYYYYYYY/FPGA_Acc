"""Presearch native timing graph/atom map only; dynamic criticality model not implemented."""
import json,hashlib,shutil,subprocess,os,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19';N=R/'build/native_external_shared_sink_native_v1_2026-10-19';D=R/'build/native_external_current_timing_graph_v1_2026-10-19';O=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';BASE=E/'prospective_external_family_native_shared_sink_native_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 b=read(N/'receipt.json');assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());D.mkdir(exist_ok=False);O.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source');f=D/'source/route.cpp';s=f.read_text();s='#include "atom_lookup.h"\n#include "clustered_netlist_utils.h"\n#include "tatum/TimingConstraints.hpp"\n'+s
 anchor='    std::unique_ptr<NetPinTimingInvalidator> pin_timing_invalidator;';assert s.count(anchor)==1
 code=r'''
    {
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
        timing_info->timing_constraints()->print_constraints();
        VTR_LOG("RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING\n");std::fflush(nullptr);std::exit(0);
    }
'''
 f.write_text(s.replace(anchor,code+anchor));p=read(B/'protocol.json');compile=[x.replace(str(B),str(D)) for x in p['compile']];link=read(N/'protocol.json')['link'];link=[str(D/'route.o') if x==str(B/'route.o') else str(D/'sequence_vpr') if x==str(N/'sequence_vpr') else x for x in link];bindings={str(N/'receipt.json'):sha(N/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for path in (D/'source').rglob('*'):
  if path.is_file():bindings[str(path)]=sha(path)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Current nominal packed mapping after initial native STA only; export typed graph/capture setup-hold values, atom pin mappings and data sink criticalities. Exit before search. Native constraints printed to log, no machine-readable constraints schema or dynamic model claimed.'),indent=2)+'\n')
 for stage,cmd in [('compile',compile),('link',link)]:
  with (D/(stage+'.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 cases=[c for c in read(BASE/'manifest.json')['cases'] if c['case'].endswith('/cold')];(O/'protocol.json').write_text(json.dumps(dict(cases=cases,bindings=bindings,scope='All3 presearch data only. No source or target route labels generated; dynamic criticality/STA equivalence after speculative path changes unproven.'),indent=2)+'\n')
 def run(c):
  case=c['case'].removesuffix('/cold');out=O/case;out.mkdir(parents=True)
  for k,name in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(c['inputs'][k],out/name)
  cmd=c['command'].copy();cmd[0]=str(D/'sequence_vpr');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
  with (out/'native.log').open('x') as log:code=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT).returncode
  same=(out/'initial_connections.tsv').exists() and sha(out/'initial_connections.tsv')==sha(BASE/case/'cold/native/initial_connections.tsv');row=dict(case=case,exit_code=code,no_route_generated=not list(out.glob('*.route')),initial_connection_bytes_equal=same,marker='RC_TIMING_GRAPH_SNAPSHOT_EXIT_BEFORE_ROUTING' in (out/'native.log').read_text());print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 assert all(sha(k)==h for k,h in bindings.items());(O/'terminal.json').write_text(json.dumps(dict(status='ALL3_PRESEARCH_TIMING_GRAPH_CAPTURE_PROCESSES_TERMINAL',rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
