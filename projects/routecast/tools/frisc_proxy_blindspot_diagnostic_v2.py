"""Posthoc covered-path/RC diagnostic; never changes frozen decisions."""
import json,time
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from path_rc import PathRC
out=Path('experiments/frisc_proxy_blindspot_diagnostic_v2_2026-10-05');root=Path('experiments/frisc_timing_backgrounds_v2_2026-10-05');contextfile=Path('experiments/frisc_bound_timing_context_2026-10-05/context.json');epath=Path('experiments/frisc_endpoints_2026-10-05/endpoints.json')
if out.exists():raise ValueError('fresh output required')
e=json.loads(epath.read_text());context=json.loads(contextfile.read_text())['context'];inputs={str(epath):sha(epath),str(contextfile):sha(contextfile),e['inputs']['graph']['path']:e['inputs']['graph']['sha256']}
files={c:root/('baseline_prediction.json' if c==0 else f'candidate_{c}_prediction.json') for c in range(9)};inputs.update({str(f):sha(f) for f in files.values()});assert all(sha(f)==h for f,h in inputs.items());start=time.monotonic();g=read_rr_graph(e['inputs']['graph']['path']);rc=PathRC(g);base={r['connection_id']:r for r in json.loads(files[0].read_text())['connections']};groups={}
for cid,r in base.items():groups.setdefault((r['net_id'],r['source'],r['sink']),[]).append(cid)
covered={tuple(v) for path in context['paths'] for v in path['endpoint_groups']};covered_ids={cid for group in covered for cid in groups[group]};base_rc={cid:rc.path(base[cid]['source'],base[cid]['physical_edge_ids']).delay for cid in covered_ids};reports=[]
for c in range(1,9):
 rows={r['connection_id']:r for r in json.loads(files[c].read_text())['connections']};assert rows.keys()==base.keys();changed={cid for cid in rows if tuple(rows[cid]['physical_edge_ids'])!=tuple(base[cid]['physical_edge_ids'])};deltas={}
 for group in covered:
  ids=groups[group];deltas[group]=max(rc.path(rows[cid]['source'],rows[cid]['physical_edge_ids']).delay for cid in ids)-max(base_rc[cid] for cid in ids)
 path_delta=[sum((deltas[tuple(group)] for group in p['endpoint_groups']),Fraction(0)) for p in context['paths']]
 reports.append({'candidate_id':c,'changed_connection_count':len(changed),'changed_covered_connection_count':len(changed&covered_ids),'changed_uncovered_connection_count':len(changed-covered_ids),'covered_groups_with_changed_path':sum(any(cid in changed for cid in groups[group]) for group in covered),'covered_groups_with_nonzero_path_rc_delta':sum(v!=0 for v in deltas.values()),'max_observed_path_rc_delta_ps':float(max(path_delta)*10**12),'max_observed_path_rc_delta_seconds_exact':str(max(path_delta))})
assert all(sha(f)==h for f,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'path_rc.py').write_text(Path('tools/path_rc.py').read_text());receipt={'reports':reports,'covered_groups':len(covered),'covered_connection_ids_count':len(covered_ids),'input_sha256':inputs,'source_sha256':sha(__file__),'rc_module_sha256':sha('tools/path_rc.py'),'wall_s':time.monotonic()-start,'limitations':['posthoc diagnostic on already evaluated candidates, no policy retuning','zero tree-start RC; connection expansion only, no branch load or complete STA','unchanged sketch path does not imply unchanged native route','baseline top100 reports only']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(reports))
