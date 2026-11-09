"""Actual native TimingConstraints multi-domain/default/override contract with parser replay."""
import json,hashlib,subprocess,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from load_native_clock_constraints_v1 import load,resolve,value,serializable
B=R/'build/native_external_clock_constraints_v1_2026-10-19';D=R/'build/native_clock_constraint_contract_v1_2026-10-19';E=R/'experiments/native_clock_constraint_contract_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);E.mkdir(exist_ok=False);source=B/'source/route.cpp';s=source.read_text();begin=s.index('        const auto& constraints=*timing_info->timing_constraints();');end=s.index('        timing_info->timing_constraints()->print_constraints();',begin);code=s[begin:end];code=code.replace('        const auto& constraints=*timing_info->timing_constraints();','');code=code.replace('for(auto node:graph.nodes())if(graph.node_type(node)==tatum::NodeType::SINK)capture(node);','for(auto node:{tatum::NodeId(100),tatum::NodeId(200),tatum::NodeId(250)})capture(node);')
 prefix=r'''
#include "tatum/TimingConstraints.hpp"
#include <cstdio>
#include <stdexcept>
int main(){
 tatum::TimingConstraints constraints;
 auto a=constraints.create_clock_domain("launch");auto b=constraints.create_clock_domain("virtual_capture");
 constraints.set_clock_domain_source(tatum::NodeId(10),a);
 constraints.set_setup_constraint(a,a,tatum::Time(10e-9f));constraints.set_hold_constraint(a,a,tatum::Time(1e-9f));
 constraints.set_setup_constraint(a,a,tatum::NodeId(100),tatum::Time(7e-9f));constraints.set_hold_constraint(a,a,tatum::NodeId(100),tatum::Time(.5e-9f));
 constraints.set_setup_constraint(a,b,tatum::Time(5e-9f));constraints.set_hold_constraint(b,a,tatum::Time(3e-9f));
 constraints.set_setup_clock_uncertainty(a,a,tatum::Time(.2e-9f));constraints.set_hold_clock_uncertainty(a,a,tatum::Time(.1e-9f));
 constraints.set_source_latency(a,tatum::ArrivalType::EARLY,tatum::Time(1e-9f));constraints.set_source_latency(a,tatum::ArrivalType::LATE,tatum::Time(2e-9f));
 constraints.set_input_constraint(tatum::NodeId(50),a,tatum::DelayType::MAX,tatum::Time(.1e-9f));
 constraints.set_output_constraint(tatum::NodeId(60),b,tatum::DelayType::MAX,tatum::Time(.2e-9f));constraints.set_constant_generator(tatum::NodeId(70),true);
'''
 f=D/'fixture.cpp';f.write_text(prefix+code+'\nreturn 0;}\n');p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());compile=p['compile'][:-4]+['-c',str(f),'-o',str(D/'fixture.o')];link=[x for x in p['link'] if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link=[str(D/'fixture.o') if x.endswith('/main.cpp.o') else str(D/'fixture') if x.endswith('/routecast_seed_vpr') else x for x in link];bindings={str(f):sha(f),str(source):sha(source),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/load_native_clock_constraints_v1.py'):sha(R/'tools/load_native_clock_constraints_v1.py')}
 for x in link:
  if x.startswith('/') and Path(x).is_file() and x!=str(D/'fixture.o'):bindings[x]=sha(x)
 (E/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,scope='Real native TimingConstraints object.2domains, virtualclock, default and capture-specific constraints, setup-only/hold-only/absent pair, uncertainties/latencies/IO/constants. Not graph STA or physical routing.'),indent=2)+'\n')
 for stage,cmd in [('compile',compile),('link',link),('run',[str(D/'fixture')])]:
  with (E/(stage+'.log')).open('x') as log:subprocess.run(cmd,cwd=E,stdout=log,stderr=subprocess.STDOUT,check=True)
 data=load(E/'clock_constraints.tsv');assert len(data['domains'])==2 and data['domains'][1]['virtual'];assert data['constants']==[70];assert len(data['native_queries'])==16
 for q in data['native_queries']:assert resolve(data,q['source'],q['sink'],q['capture'])=={k:q[k] for k in ['setup','hold','analyze']}
 for q in data['native_latency_queries']:assert q['value']==data['latencies'].get((q['kind'],q['domain']),value('0'))
 for q in data['native_uncertainty_queries']:
  for mode in ('SETUP','HOLD'):assert q[mode.lower()]==data['uncertainties'].get((mode,q['source'],q['sink']),value('0'))
 assert resolve(data,0,0,100)['setup']==value('7e-9') and resolve(data,0,0,200)['setup']==value('10e-9');assert not resolve(data,1,1)['analyze'];assert not resolve(data,0,1)['hold']['defined'];assert not resolve(data,1,0)['setup']['defined']
 machine=E/'clock_constraints.json';machine.write_text(json.dumps(serializable(data),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(E/'verification.json').write_text(json.dumps(dict(status='ACTUAL_NATIVE_TWO_DOMAIN_CLOCK_CONSTRAINT_OVERRIDE_DEFAULT_AND_UNDEFINED_CONTRACT_PASS',domains=2,setup_hold_capture_queries=16,source_latency_queries=4,uncertainty_queries=4,bindings={**bindings,str(E/'clock_constraints.tsv'):sha(E/'clock_constraints.tsv'),str(machine):sha(machine),str(D/'fixture'):sha(D/'fixture')},scope='Actual compiled native constraints API+snapshot export+independent resolver. Synthetic numeric node IDs, not clock graph propagation/STA, pin-remap invariance or forecast acceptance.'),indent=2)+'\n');print('NATIVE_CLOCK_CONSTRAINT_CONTRACT_PASS')
if __name__=='__main__':main()
