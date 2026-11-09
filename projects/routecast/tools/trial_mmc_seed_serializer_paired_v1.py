"""Three alternating full MMC serialization subprocess pairs, no retries."""
import json,sys,time,subprocess,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
B=R/'experiments/ultraembedded_mmc_continuous_workflow_v3_2026-10-08/seed'
if len(sys.argv)>1:
 from shared_compact_native_inventory_v1 import Inventory
 mode,out=sys.argv[1],Path(sys.argv[2]);out.mkdir()
 if mode=='baseline':from serialize_whole_net_subset_v1 import serialize_subset
 elif mode=='candidate':from serialize_whole_net_subset_pin_index_v2 import serialize_subset
 else:raise ValueError(mode)
 candidate=json.loads((B/'native/mmc/subset.json').read_text());inv=Inventory(B/'rr/mmc/rr_graph.xml')
 text,pins=serialize_subset(candidate,B/'demand/mmc/endpoints.json',B/'demand/mmc/identity.jsonl',B/'native/mmc/design.place',inv)
 (out/'seed.route').write_text(text);(out/'bindings.json').write_text(json.dumps(pins)+'\n');sys.exit(0)
D=R/'experiments/mmc_seed_serializer_paired_v1_2026-10-08';D.mkdir()
proof=R/'experiments/mmc_seed_serializer_pin_index_v3_2026-10-08/verification.json';reject=R/'experiments/seed_serializer_rejections_v1_2026-10-08/verification.json'
bindings=closure([Path(__file__),R/'tools/serialize_whole_net_subset_v1.py',R/'tools/serialize_whole_net_subset_pin_index_v2.py',R/'tools/shared_compact_native_inventory_v1.py'])
for p in [proof,reject]:
 data=json.loads(p.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings.update(data['bindings']);bindings[str(p)]=sha(p)
for p in [B/'native/mmc/subset.json',B/'rr/mmc/rr_graph.xml',B/'demand/mmc/endpoints.json',B/'demand/mmc/identity.jsonl',B/'native/mmc/design.place',B/'native/mmc/seed.route',B/'native/mmc/bindings.json']:bindings[str(p)]=sha(p)
orders=[['baseline','candidate'],['candidate','baseline'],['baseline','candidate']]
protocol=dict(bindings=bindings,orders=orders,timer='Parent perf_counter around fresh child process, includes imports, input JSON/XML/hash load, full serializer checks and file writes; excludes parent output parity and source authentication.',scope='Known full MMC selected seed, three alternating orders not perfectly balanced, shared host, no statistical/fullworkflow inference.',timeout_seconds=1200)
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for pair,order in enumerate(orders):
 for mode in order:
  out=D/f'{pair}_{mode}';row=dict(pair=pair,mode=mode,status='RUNNING');rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n')
  tick=time.perf_counter()
  try:
   with (D/f'{pair}_{mode}.log').open('w') as f:
    p=subprocess.run([sys.executable,str(Path(__file__)),mode,str(out)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
   seconds=time.perf_counter()-tick;assert p.returncode==0,p.returncode
   assert (out/'seed.route').read_bytes()==(B/'native/mmc/seed.route').read_bytes()
   assert json.loads((out/'bindings.json').read_text())==json.loads((B/'native/mmc/bindings.json').read_text())
   assert all(sha(k)==v for k,v in bindings.items())
   row.update(status='FULL_SERIALIZATION_PARITY_PASS',subprocess_seconds=seconds,files={str(p):sha(p) for p in out.iterdir() if p.is_file()})
  except Exception as error:
   row.update(status='FAILED_OR_TIMEOUT',error=repr(error),elapsed_seconds=time.perf_counter()-tick)
  (D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row['pair'],mode,row['status'],row.get('subprocess_seconds'),flush=True)
  if row['status']!='FULL_SERIALIZATION_PARITY_PASS':sys.exit(1)
ratios=[next(r['subprocess_seconds'] for r in rows if r['pair']==i and r['mode']=='candidate')/next(r['subprocess_seconds'] for r in rows if r['pair']==i and r['mode']=='baseline') for i in range(3)]
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,ratios=ratios,median=statistics.median(ratios),scope=protocol['scope']),indent=2)+'\n');print('ratios',ratios,flush=True)
