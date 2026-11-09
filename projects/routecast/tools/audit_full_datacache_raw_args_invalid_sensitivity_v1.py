import hashlib,itertools,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'experiments/full_original_source_proc_state_v1_2026-10-09/source_proc.json';V=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));names=['dataCache_1_io_cpu_execute_args_wr','dataCache_1_io_cpu_execute_args_size'];cells={};cases=[]
for name in names:
 bits=m['netnames'][name]['bits'];matches=[(n,c) for n,c in m['cells'].items() if c['connections'].get('Y')==bits];assert len(matches)==1;n,c=matches[0];assert c['type']=='$mux' and c['connections']['S']==m['netnames']['MmuPlugin_dBusAccess_cmd_valid']['bits'];cells[n]=c
 if name.endswith('wr'):assert c['connections']['A']==[2029]
 else:assert c['connections']['A']==[2727,2728]
 for values in itertools.product('01x',repeat=len(bits)):
  # Actual mux S0 always returns A. Valid is not an input to these muxes.
  cases.append({'signal':name,'execute_valid':'0','mmu_cmd_valid':'0','pipeline_argument':''.join(reversed(values)),'raw_argument':''.join(reversed(values))})
lines=V.read_text().splitlines();out={'actual_muxes':cells,'known_no_mmu_cases':cases,'binary_sensitivity_witness':{'execute_valid':'0','mmu_cmd_valid':'0','left_execute_wr':'0','right_execute_wr':'1','left_raw_args_wr':'0','right_raw_args_wr':'1'},'source_blocks':{'wr':lines[3886:3895],'size':lines[3909:3918]},'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,V]},'scope':'Actual raw DataCache argument muxes are sensitive to invalid pipeline data when MMU command0. This is a local cut-boundary counterexample to blanket raw-value masking, not a reachable reset trace or proof that valid-gated downstream operations fail. Full downstream consumer proof remains necessary.'};D=R/'experiments/full_datacache_raw_args_invalid_sensitivity_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'sensitivity_audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Actual two muxes:12 known-no-MMU 0/1/X cases; raw args are not masked by execute-valid')
