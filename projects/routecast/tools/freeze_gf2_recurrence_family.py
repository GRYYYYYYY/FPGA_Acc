"""New locally generated GF2 recurrence family, frozen before native routing."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_recurrence_family_freeze_2026-10-06';out.mkdir();(out/'source').mkdir()
widths=[32,64,128];bits=32;taps=[0,1,4,7,12,16,23,31]
for name in ['freeze_gf2_recurrence_family.py','joint_prediction_engine.py','persistent_rc_context.py','frontier_repair_engine.py','moved_history_repair_engine.py','staged_placement_reroute.py','route_ledger_state.py','native_capacity_rc_search.py','nonzero_rc_endpoint_context.py','pre_route_endpoints.py']:
 shutil.copyfile(root/'tools'/name,out/'source'/name)
shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';binary=shared/'build_tileplace_vpr/vpr/vpr';availability=json.loads((root/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());yosys=Path(availability['yosys_path']);abc=yosys.parent.parent/'abc/abc'
p={'family':'local GF2 left-shift/data-feedback recurrence','state_bits':bits,'tap_indices':taps,'input_widths':widths,'semantics':'For each ascending data bit, feedback=old_state[31] XOR data_bit; shift old_state left by1, then XOR feedback into exactly tap positions. No standardized CRC or primitive polynomial claim.','split':'All generated widths share one family and are held out together from recorded ex5p/tseng/synthetic arithmetic development. No within-family tuning or best-case selection.','local_provenance':'New generator in this turn; absence in prior named tools/plan is not universal exposure proof. Prospective only relative to frozen local policy.','sources_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')},'native_inputs_sha256':{str(p):sha(p) for p in (arch,binary,abc)},'policy':{'seed':1,'channel_width':128,'workers':1,'max_router_iterations':100,'native_timeout_s':180,'predictor_branch_budget_ns':1,'predictor_max_labels':10000,'predictor_fallback_limit':64,'order':'ascending net/CID','cost':'unchanged exact buffered RC delay*(otherNET demand+1)','placement_update':'first two compatible packed-order CLBs, no metric-driven selection','repair':'unchanged inherited history max4 frontier releases on UNREACHABLE'},'required_evidence':['independent integer recurrence oracle versus generated BLIF','ABC combinational equivalence to LUT6 mapped BLIF','native FULL/STA and original XML physical audit','pre-route endpoints and nonzero bufferedRC compatibility','frozen predictor complete/failure retained without tuning','real placement update/native matched reference/quality gate','full preparation/search/failure/repair/native/fallback cost','resource prediction rank/topset and route quality'], 'no_route_or_timing_labels_in_generation':True,'status':'inputs/source/policy frozen before any native route on this family'}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');records=[]
for width in widths:
 directory=out/f'gf2_d{width}';directory.mkdir();inputs=[f's_{i}' for i in range(bits)]+[f'd_{i}' for i in range(width)];outputs=[f'y_{i}' for i in range(bits)];lines=['.model gf2_recurrence','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs)];state=inputs[:bits]
 for step in range(width):
  fb=f'f_{step}';lines.extend([f'.names {state[-1]} d_{step} {fb}','01 1','10 1']);next_state=[]
  for bit in range(bits):
   name=f'n_{step}_{bit}';next_state.append(name)
   if bit==0:lines.extend([f'.names {fb} {name}','1 1'])
   elif bit in taps:lines.extend([f'.names {state[bit-1]} {fb} {name}','01 1','10 1'])
   else:lines.extend([f'.names {state[bit-1]} {name}','1 1'])
  state=next_state
 for name,value in zip(outputs,state):lines.extend([f'.names {value} {name}','1 1'])
 lines.append('.end');path=directory/'generated.blif';path.write_text('\n'.join(lines)+'\n');records.append({'width':width,'path':str(path.resolve()),'sha256':sha(path),'family':p['family']})
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'records':records,'generator_sha256':sha(Path(__file__)),'native_routing_started':False},indent=2)+'\n');print('frozen GF2 family widths',widths)
