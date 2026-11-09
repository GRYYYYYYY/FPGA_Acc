"""Fresh serial prepared-input cold-only baseline with equal selected-state proof."""
import json,time,runpy,contextlib
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_screened4_cold_cost_baseline_2026-10-07';out.mkdir()
files=['capture_bitonic_swapped_cold.py','verify_bitonic_swapped_cold.py','trial_bitonic_swapped_cold_n4_canonical.py','trial_bitonic_swapped_cold_n8_canonical.py','trial_bitonic_swapped_cold_n16_canonical.py','verify_bitonic_swapped_cold_canonical.py','trial_bitonic_selected_state.py','verify_bitonic_selected_state.py'];paths={}
for name in files:
 src=ROOT/'tools'/name
 if 'n16_canonical' in name:
  text=(ROOT/'tools/trial_bitonic_swapped_cold_n8_canonical.py').read_text().replace('cold_n8','cold_n16').replace("x['count']==8","x['count']==16").replace("parent/'n8'","parent/'n16'").replace('==1514','==5070')
 else:text=(ROOT/'tools/verify_native_cold_only.py').read_text() if name=='verify_bitonic_swapped_cold.py' else src.read_text()
 text=text.replace('owner_union_wire_rc_context_cached','owner_union_wire_rc_context_cached_tree')
 text=text.replace('bitonic_swapped_cold','bitonic_screened4_baseline_swapped_cold').replace('bitonic_selected_state','bitonic_screened4_baseline_selected_state').replace('bitonic_resident_staging_n','bitonic_workflow_screened4_resident_staging_n').replace('bitonic_resident_staging_native_import','bitonic_workflow_screened4_resident_staging_native_import')
 if name=='verify_bitonic_swapped_cold_canonical.py':text=text.replace('[(4,371),(8,1514)]','[(4,371),(8,1514),(16,5070)]')
 if name=='trial_bitonic_selected_state.py':text=text.replace('candidate iff CPD <= cold AND wirelength <= cold, native reported precision','cold-only baseline, all cases').replace("accept=F(ref['candidate_cpd_ns'])<=F(ref['cold_cpd_ns']) and ref['candidate_wirelength']<=ref['cold_wirelength']",'accept=False')
 if name=='verify_bitonic_selected_state.py':text=text.replace("('candidate' if ref['joint_nonregression'] else 'cold')","'cold'")

 if name=='trial_bitonic_selected_state.py':
  start=text.index(';can=ROOT/');end=text.index('\n accept=False',start);text=text[:start]+';candidate=None'+text[end:]
 name2=name.replace('bitonic_swapped_cold','bitonic_screened4_baseline_swapped_cold').replace('bitonic_selected_state','bitonic_screened4_baseline_selected_state');target=ROOT/'tools'/name2;assert not target.exists();target.write_text(text);paths[name]=target
from freeze_priority_family import closure
p=dict(sources=closure([Path(__file__),*paths.values()]),scope='Fresh cold route-only all3 same fixed target layouts, independent physical proof, canonical all3 reload/path proof, selected endpoint/ledger/FULL STA. No seed ledger/prediction required. Equal cached RR implementation; cache cleared at baseline start; OS/module cache not reset. Mapped netlist/target layouts/graph available inputs. Single serial observation, no raw-input end-to-end claim.')
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');from cached_rr_endpoint_context_tree import clear_cache
clear_cache();tick=time.perf_counter();rows=[]
for name in files:
 start=time.perf_counter()
 with (out/(name+'.log')).open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):runpy.run_path(str(paths[name]),run_name='__main__')
 rows.append(dict(stage=name,seconds=time.perf_counter()-start,log_sha256=sha(out/(name+'.log'))));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=False),indent=2)+'\n');print(name,rows[-1]['seconds'],flush=True)
assert all(sha(f)==h for f,h in p['sources'].items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=True,baseline_seconds=time.perf_counter()-tick),indent=2)+'\n')
