"""Reuse immutable audited payloads only after result and seed identity checks."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];old=ROOT/'experiments/mux_online_loop_2026-10-06';new=ROOT/'experiments/mux_critical_release_online_loop_2026-10-06';op=json.loads((old/'protocol.json').read_text());np=json.loads((new/'protocol.json').read_text());names=('control_timing_verification','physical_budget_verification','floor_verification','choice_verification','observation_verification');rows=[]
for oc,nc in zip(op['cases'],np['cases']):
 assert oc==nc
 w,i=nc['width'],nc['index'];rel=Path(f'w{w}_m{i}');src=old/rel/'result.json';dst=new/rel/'result.json'
 if not src.exists() or not dst.exists():continue
 assert sha(src)==sha(dst)
 original=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';seed=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(original.read_text());b=json.loads(seed.read_text());assert a['floor_ns']==b['floor_ns'] and a['affected']['affected_complete_net_connection_ids']==b['expanded_connection_ids'] and not b['added_nets'];assert all(a[k]==b[k] for k in ('graph_sha256','mapping_sha256','target_cpd_ns'));assert all(sha(f)==h for f,h in nc['inputs'].items())
 audits={}
 for name in names:
  src_a=old/rel/(name+'.json');d=json.loads(src_a.read_text());assert d['result_sha256']==sha(dst);dest_a=new/rel/(name+'.json');shutil.copyfile(src_a,dest_a);audits[str(src_a)]=sha(src_a)
 manifest=dict(result_sha256=sha(dst),old_result_sha256=sha(src),old_seed_sha256=sha(original),new_seed_sha256=sha(seed),source_sha256=sha(Path(__file__)),audits=audits,scope='Proof reuse by byte-identical result payload, identical original targets and exact seed floor/release/model parameters. No new solver/audit execution or old timing measurement relabelled.')
 (new/rel/'audit_reuse.json').write_text(json.dumps(manifest,indent=2)+'\n');rows.append(dict(width=w,index=i,result_sha256=sha(dst)));print(w,i,'reused validated identical-result evidence',flush=True)
(new/'audit_reuse_summary.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),rows=rows),indent=2)+'\n')
