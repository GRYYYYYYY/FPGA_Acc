"""Original XML re-audit plus joint net-union structure for frozen move predictions."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
from streaming_prediction_audit import verify

base=Path('experiments');sequence=base/'adder_tree_2L032_move_sequence_2026-10-06';pred=base/'adder_tree_2L032_move_sequence_audit_2026-10-06';native=base/'native_pressure_move_sequence_trial_2026-10-06'
out=base/'adder_tree_2L032_move_topology_diagnosis_2026-10-06';out.mkdir();(out/'source').mkdir()
protocol=json.loads((sequence/'protocol.json').read_text());receipt=json.loads((pred/'receipt.json').read_text());nr=json.loads((native/'receipt.json').read_text());assert nr['protocol_sha256']==sha(native/'protocol.json');bindings={str(pred/'receipt.json'):sha(pred/'receipt.json'),str(native/'receipt.json'):sha(native/'receipt.json'),str(sequence/'protocol.json'):sha(sequence/'protocol.json')}
for name in ('diagnose_move_sequence_topology.py','streaming_prediction_audit.py','net_union_topology.py','physical_prediction_audit.py','pre_route_endpoints.py'):
 shutil.copyfile(Path('tools')/name,out/'source'/name);bindings[str(Path('tools')/name)]=sha(Path('tools')/name)
results=[]
for item in receipt['steps']:
 i=item['step'];prediction_path=pred/f'step_{i}_prediction.json';assert sha(prediction_path)==item['prediction_sha256'];ep_path=sequence/f'step_{i}_endpoints.json';e=json.loads(ep_path.read_text());p=json.loads(prediction_path.read_text());result=verify(protocol['inputs']['rr_graph']['path'],e,p,topology=True);assert result['all_physical_and_union_checks_passed']
 topology=result['net_union_topology'];report=out/f'step_{i}.json';report.write_text(json.dumps(result,indent=2)+'\n');bindings[str(prediction_path)]=sha(prediction_path);bindings[str(ep_path)]=sha(ep_path)
 row={'step':i,'nets':topology['net_count'],'internal_reconvergent_nets':topology['internal_reconvergent_net_count'],'cyclic_nets':topology['cyclic_net_count'],'terminal_alias_nets':topology['terminal_alias_net_count'],'predicted_channel_overuse_units':result['predicted_channel_overuse_units'],'report_sha256':sha(report)};results.append(row);print(json.dumps(row),flush=True)
assert all(sha(path)==digest for path,digest in bindings.items())
(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'results':results,'scope':'post-outcome diagnostic; union structural counts do not certify complete native legality or causality. No feedback coefficient tuning or prospective gating benefit.'},indent=2)+'\n')
