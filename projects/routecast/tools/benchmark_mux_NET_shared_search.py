"""Fresh ABBA largest-case benchmark; exact serialized policy parity each run."""
import json,time,platform
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from pressure_capacity_forecast import forecast as original
from net_shared_capacity_forecast import forecast as shared
root=Path(__file__).resolve().parents[1]
base=root/'experiments/mux_NET_shared_search_2026-10-06'
p=json.loads((base/'protocol.json').read_text())
c=next(c for c in p['cases'] if c['data_width']==32 and c['channels']==128)
assert sha(c['endpoint_path'])==c['endpoint_sha256']
assert sha(c['baseline'])==c['baseline_sha256']
out=root/'experiments/mux_NET_shared_ABBA_2026-10-06';out.mkdir()
protocol={'case':c,'order':['original','shared','shared','original'],'sources_sha256':{n:sha(root/'tools'/n) for n in ['benchmark_mux_NET_shared_search.py','pressure_capacity_forecast.py','net_shared_capacity_forecast.py','persistent_rc_context.py']},'python':platform.python_version(),'scope':'Largest mux case selected to test scaling; one shared immutable context setup outside timed searches, fresh forecast state every invocation. Fixed ABBA order, no warmup or stopping based on timing. All four results retained and serialized independently. Search only, not total pipeline; single ABBA block is not statistical generalization.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
t=time.monotonic();ctx=PersistentRCContext(c['endpoint_path']);setup=time.monotonic()-t
old=json.loads(Path(c['baseline']).read_text());rows=[]
for i,name in enumerate(protocol['order']):
 t=time.monotonic();q=(original if name=='original' else shared)(ctx,True);elapsed=time.monotonic()-t
 file=out/f'{i}_{name}.json';file.write_text(json.dumps(q,indent=2)+'\n');loaded=json.loads(file.read_text())
 assert {k:v for k,v in loaded.items() if k!='events'}=={k:v for k,v in old.items() if k!='events'}
 assert [{k:v for k,v in e.items() if k!='expanded'} for e in loaded['events']]==[{k:v for k,v in e.items() if k!='expanded'} for e in old['events']]
 row={'index':i,'implementation':name,'search_s':elapsed,'output_sha256':sha(file),'expanded_nodes':sum(e['expanded'] for e in q['events']),'semantic_parity':True};rows.append(row)
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'setup_s':setup,'rows':rows,'complete':len(rows)==4},indent=2)+'\n');print(row,flush=True)
