import json,sys,ast,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_native_demand_uniform_channel_v1_2026-10-08';rp=out/'prediction_comparison.json';d=json.loads(rp.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());source=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';tree=ast.parse(source.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='audit_metric');scope=dict(Counter=Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(source),'exec'),scope);bindings={str(rp):sha(rp),str(source):sha(source),str(Path(__file__)):sha(Path(__file__))}
for row in d['rows']:
 p=out/row['name']/'comparison_vectors.json';v=json.loads(p.read_text());bindings[str(p)]=sha(p);p=out/row['name']/'resident/sketch.json';s=json.loads(p.read_text());bindings[str(p)]=sha(p);assert row['required']==row['completed']==s['required_connections']==s['completed_connections']
 c=v['channels'];b=v['bins'];assert all(x['predictions']['uniform_shared']==s['ledger'].get(str(x['node']),0) for x in c)
 scope['audit_metric']({x['node']:x['predictions']['uniform_shared']/x['capacity'] for x in c},{x['node']:x['native']/x['capacity'] for x in c},row['uniform_shared']['concrete'],len(c)//20)
 scope['audit_metric']({tuple(x['key']):x['predictions']['uniform_shared']/x['capacity'] for x in b},{tuple(x['key']):x['native']/x['capacity'] for x in b},row['uniform_shared']['spatial'],20)
assert scope['checked']==4 and all(sha(k)==v for k,v in bindings.items())
(out/'metric_verification.json').write_text(json.dumps(dict(bindings=bindings,metric_groups=4,histogram_ranks_mae_topk_pass=True,scope='Independent histogram metric implementation reused by source-bound AST function; full native universe certified by prior vector audit, uniform spatial mapping checked by evaluator against original XML. Not a second independent XML spatial proof.'),indent=2)+'\n');print('PASS uniform metrics',scope['checked'])
