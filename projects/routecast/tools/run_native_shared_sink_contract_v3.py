"""Fixture uses real native CBRR constructor/setter/force/flags; only timing getter wrapped."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'build/native_shared_sink_contract_v3_2026-10-19';E=R/'experiments/native_shared_sink_contract_v3_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 E.mkdir(exist_ok=False);p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());fixed=R/'build/native_external_delay_bound_index_v1_2026-10-19';b=json.loads((fixed/'receipt.json').read_text());assert all(sha(k)==h for k,h in b['bindings'].items());compile=p['compile'][:-4]+['-c',str(D/'fixture.cpp'),'-o',str(D/'fixture.o')];bindings={str(D/'fixture.cpp'):sha(D/'fixture.cpp'),str(Path(__file__).resolve()):sha(__file__),str(fixed/'receipt.json'):sha(fixed/'receipt.json')};commands={}
 link=[x for x in p['link'] if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link=[str(D/'fixture.o') if x.endswith('/main.cpp.o') else str(R/'build/native_candidate_move_accept_scoped_2026-10-06/libvpr.a') if x.endswith('/libvpr.a') else x for x in link];symbol='_Z33calculate_clb_net_pin_criticalityRK15SetupTimingInfoRK26ClusteredPinAtomPinsLookupN3vtr8StrongIdI18general_pin_id_tagiLin1EEEb'
 for x in link:
  if x.startswith('/') and Path(x).is_file() and x!=str(D/'fixture.o'):bindings[x]=sha(x)
 with (E/'compile.log').open('x') as log:subprocess.run(compile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 group_compile=p['compile'][:-4]+['-c',str(D/'connection_based_routing.cpp'),'-o',str(D/'group_or.o')]
 with (E/'group_compile.log').open('x') as log:subprocess.run(group_compile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 bindings[str(D/'connection_based_routing.cpp')]=sha(D/'connection_based_routing.cpp');bindings[str(D/'connection_based_routing.h')]=sha(D/'connection_based_routing.h');bindings[str(D/'group_or.o')]=sha(D/'group_or.o')
 for arm in ['original','own_index_fixed','own_index_group_or']:
  exe=D/arm;cmd=[str(exe) if x.endswith('/routecast_seed_vpr') else x for x in link];cmd.insert(1,'-Wl,--wrap='+symbol)
  if arm=='own_index_fixed':cmd.insert(1,str(fixed/'connection_based_routing.o'));bindings[str(fixed/'connection_based_routing.o')]=sha(fixed/'connection_based_routing.o')
  if arm=='own_index_group_or':cmd.insert(1,str(D/'group_or.o'))
  commands[arm]=cmd
 (E/'protocol.json').write_text(json.dumps(dict(compile=compile,link=commands,bindings=bindings,scope='7 scenarios use real Netlist and real compiled CBRR; synthetic RR terminal IDs and deterministic substituted timing criticality only. Not physical/canonical route or QoR evidence.'),indent=2)+'\n')
 for arm,cmd in commands.items():
  with (E/(arm+'.build.log')).open('x') as log:subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
  with (E/(arm+'.tsv')).open('x') as log:subprocess.run([str(D/arm)],cwd=E,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==h for k,h in bindings.items());print('ACTUAL_NATIVE_FIXTURES_EXECUTED')
if __name__=='__main__':main()
