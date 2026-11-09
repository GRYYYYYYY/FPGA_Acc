"""Read-only all-pin force-reroute call contract observer on corrected own-pin bounds."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_delay_bound_index_v1_2026-10-19';D=R/'build/native_external_delay_bound_contract_observer_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text());b=json.loads((B/'receipt.json').read_text());assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());D.mkdir(exist_ok=False);(D/'source').mkdir();s=(B/'source/connection_based_routing.cpp').read_text();s='#include <cstdio>\n#include <stdexcept>\n'+s
 anchor='    bool any_connection_rerouted = false;';assert s.count(anchor)==1
 pre=r'''
    struct BoundRow {ParentNetId net;int pin;RRNodeId sink;float bound;float delay;float crit;bool flag;};
    std::vector<BoundRow> bound_rows;
    for(auto net:net_list_.nets())for(auto pin:net_list_.net_sinks(net)) {
        int index=net_list_.pin_net_index(pin);auto sink=net_terminals_[net][index];float bound=lower_bound_connection_delay[net][index];float delay=net_delay[net][index];
        float crit=(bound!=0 && !(delay<bound))?calculate_clb_net_pin_criticality(*timing_info,netlist_pin_lookup,pin,is_flat_):-1.f;
        bound_rows.push_back({net,index,sink,bound,delay,crit,should_force_reroute_connection(net,sink)});
    }
'''
 s=s.replace(anchor,pre+anchor)
 end='    return !any_connection_rerouted;';assert s.count(end)==1
 post=r'''
    static size_t bound_call=0;++bound_call;
    FILE* f=std::fopen("delay_bound_calls.tsv",bound_call==1?"wx":"a");if(!f)throw std::runtime_error("bound observer open");
    std::fprintf(f,"H\t%zu\t%.9g\t%.9g\t%.9g\t%d\n",bound_call,double(max_criticality),double(connection_criticality_tolerance),double(connection_delay_optimality_tolerance),int(!any_connection_rerouted));
    for(const auto& row:bound_rows)std::fprintf(f,"P\t%zu\t%zu\t%d\t%zu\t%.9g\t%.9g\t%.9g\t%d\t%.9g\t%d\n",bound_call,size_t(row.net),row.pin,size_t(row.sink),double(row.bound),double(row.delay),double(row.crit),int(row.flag),double(lower_bound_connection_delay[row.net][row.pin]),int(should_force_reroute_connection(row.net,row.sink)));
    if(std::fclose(f))throw std::runtime_error("bound observer close");
'''
 s=s.replace(end,post+end);f=D/'source/connection_based_routing.cpp';f.write_text(s);(D/'source/connection_based_routing.h').write_bytes((B/'source/connection_based_routing.h').read_bytes());compile=[x.replace(str(B),str(D)) for x in p['compile']];link=[str(D/'connection_based_routing.o') if x==str(B/'connection_based_routing.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in p['link']];bindings={str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__),str(f):sha(f),str(f.with_suffix('.h')):sha(f.with_suffix('.h'))}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='All pin own-bound/conditional raw-criticality captured before each actual forcibly_reroute_connections; own bound/final perNET RR-SINK flag captured after original function. Cold/seed all3 fixed; read-only output equivalence required. Shared RR-SINK final flags may differ from perpin eligibility.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT')
if __name__=='__main__':main()
