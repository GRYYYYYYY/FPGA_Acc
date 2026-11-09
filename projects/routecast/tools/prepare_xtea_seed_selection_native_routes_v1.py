"""Bind both development ordering subsets to archived native terminal identities."""
import json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
R=Path(__file__).resolve().parents[1];P=R/'experiments/xtea_seed_selection_order_v1_2026-10-09';receipt=P/'receipt.json';r=json.loads(receipt.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());epfile=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'));ep=json.loads(epfile.read_text());assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());graph=Path(ep['inputs']['graph']['path']);identity=Path(ep['inputs']['native_identity']['path']);place=Path(ep['inputs']['place']['path']);inv=Inventory(graph)
D=R/'experiments/xtea_seed_selection_native_routes_v1_2026-10-09';D.mkdir();rows=[];bindings={**closure([Path(__file__)]),str(receipt):sha(receipt),str(epfile):sha(epfile),**{v['path']:v['sha256'] for v in ep['inputs'].values()}}
for row in r['rows']:
 policy=row['policy'];sp=P/(policy+'.json');assert sha(sp)==row['output_sha256'];bindings[str(sp)]=sha(sp);w=D/policy;w.mkdir();tick=time.perf_counter()
 try:
  candidate=json.loads(sp.read_text());text,pins=serialize_subset(candidate,epfile,identity,place,inv);assert len(pins)==len(candidate['records']);assert set(pins)=={x['connection_id'] for x in candidate['records']};(w/'seed.route').write_text(text);(w/'bindings.json').write_text(json.dumps(pins)+'\n');rows.append(dict(policy=policy,status='IDENTITY_AND_TREE_SERIALIZATION_PASS',connections=len(pins),seconds=time.perf_counter()-tick))
 except Exception as error:rows.append(dict(policy=policy,status='REJECTED',error=repr(error),seconds=time.perf_counter()-tick))
 assert all(sha(p)==h for p,h in bindings.items())
files={str(p):sha(p) for p in D.rglob('*') if p.is_file()}
out=dict(bindings=bindings,files=files,rows=rows,scope='Archived XTEA development subsets bound to exact original native pin identities and serialized with cycle/branch/single-parent checks. No native import/full routing/canonical admission, heldout or gain proof. All omitted connections remain native-required work; no concurrency routing benchmark launched.')
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows,indent=2))
