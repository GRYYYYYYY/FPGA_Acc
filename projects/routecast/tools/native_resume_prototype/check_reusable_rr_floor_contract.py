"""Independent negative publication and caller-aliasing checks."""
import copy,json,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_reusable_rr_floor_contract_2026-10-07';out.mkdir(exist_ok=False);binary=out/'private_binary';original=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor';shutil.copyfile(original,binary);binary.chmod(0o755)
ep=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w16_m1/target_endpoints.json';subset=json.loads((ROOT/'experiments/native_resume_critical_rr_floors_w16_m1_2026-10-07/protocol.json').read_text());selected=set(subset['selection']['selected_connection_ids']);meta=json.loads(ep.read_text());meta['connections']=[q for q in meta['connections'] if q['connection_id'] in selected];target=out/'selected.json';target.write_text(json.dumps(meta));ctx=ReusableRRFloors(target,binary,out/'context');a=ctx.query(target);snapshot=copy.deepcopy(ctx._cache);first=a['answers'][0]['minimum_integer'];a['answers'][0]['minimum_integer']=-1;a['answers'][0]['physical_edge_ids'].clear();b=ctx.query(target);assert b['answers'][0]['minimum_integer']==first and ctx._cache==snapshot and b['miss_pairs']==0
rows=[dict(case='caller mutation isolated',passed=True)];epoch=ctx.epoch
for name,modify in [('duplicate connection id',lambda d:d['connections'].__setitem__(1,copy.deepcopy(d['connections'][0]))),('invalid RR endpoint',lambda d:d['connections'][0].__setitem__('sink',ctx.n)),('wrong graph digest',lambda d:d.__setitem__('graph_sha256','0'*64))]:
 d=copy.deepcopy(meta);modify(d);f=out/(name.replace(' ','_')+'.json');f.write_text(json.dumps(d))
 try:ctx.query(f);raise AssertionError('missing rejection')
 except ValueError:pass
 assert ctx.epoch==epoch and ctx._cache==snapshot;rows.append(dict(case=name,passed=True))
data=binary.read_bytes();binary.write_bytes(data+b'tampered')
try:ctx.query(target);raise AssertionError('missing binary mismatch rejection')
except ValueError:pass
assert ctx.epoch==epoch and ctx._cache==snapshot;binary.write_bytes(data);c=ctx.query(target);assert c['miss_pairs']==0 and ctx._cache==snapshot and ctx.epoch==epoch+1;rows.append(dict(case='binary changed rejected; restored binary reuses valid cache',passed=True))
assert sha(original)==sha(binary)
(out/'verification.json').write_text(json.dumps(dict(rows=rows,verifier_sha256=sha(Path(__file__)),context_bindings=ctx.bindings,scope='Five independent cache publication/aliasing/input-model checks; valid queries cover selected53 only. Failed subprocess/IO retry and concurrent writers not covered.'),indent=2)+'\n');print('Five independent cache contract checks passed.')
