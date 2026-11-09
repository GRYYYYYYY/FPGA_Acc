"""Native interface repair trial; archived model cost excluded, no full workflow speed claim."""
import os,json,shutil,subprocess,sys,re,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from serialize_whole_net_subset_v1 import serialize_subset
from shared_compact_native_inventory_v1 import Inventory
from stream_native_route_audit import audit
from audit_native_route import NET
from canonical_reload_identity_only_v2 import canonical_reload
out=R/'experiments/aes_cold_partition_audit_v1_2026-10-08';out.mkdir();src=R/'experiments/aes_mapped_full_workflow_v1_2026-10-08';ids=R/'experiments/aes_ignored_identity_v1_2026-10-08';vpr=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml'
bindings={str(p):sha(p) for p in [Path(__file__),vpr,arch,src/'receipt.json',ids/'receipt.json']};rows=[]
for receipt in [src/'receipt.json',ids/'receipt.json']:
 data=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in data['bindings'].items())
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'policy':'Original all-query endpoints and archived model unchanged; native ignored flags captured before routing explicitly partition demand. Whole ignored NET seeds withheld, no VPR modification. Same frozen selector output for routable NETs, original budgets, width128 seed1 worker1 max100. Both cases retained. Posthoc cold audit only, excludes complete fresh workflow speed claims; original HDL equivalence unproven.'},indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for name in ['aes_cipher','aes_inv_cipher']:
 w=out/name;w.mkdir();row={'name':name,'status':'FAILED'};start=time.perf_counter()
 try:
  epfile=src/name/'endpoints.json';ep=json.loads(epfile.read_text());table=ids/name/'identity.jsonl';ident={x['name']:x for x in map(json.loads,table.read_text().splitlines())};ignored={n for n,x in ident.items() if x['ignored']}
  queries=ep['connections'];physical=[q for q in queries if ep['net_names'][str(q['net_id'])] not in ignored];nonphysical=[q for q in queries if ep['net_names'][str(q['net_id'])] in ignored]
  oldsubset=json.loads((src/name/'subset.json').read_text());kept=[q for q in oldsubset['records'] if ep['net_names'][str(q['net_id'])] not in ignored];removed=[q for q in oldsubset['records'] if ep['net_names'][str(q['net_id'])] in ignored];assert len(kept)+len(removed)==len(oldsubset['records']) and len(physical)+len(nonphysical)==len(queries)
  (w/'partition.json').write_text(json.dumps({'all_connection_ids':[q['connection_id'] for q in queries],'physical_connection_ids':[q['connection_id'] for q in physical],'ignored_connection_ids':[q['connection_id'] for q in nonphysical],'ignored_NET_names':sorted(ignored),'removed_seed_connection_ids':[q['connection_id'] for q in removed],'retained_seed_connection_ids':[q['connection_id'] for q in kept]})+'\n')
  for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/name/f,w/f)
  graph=Path(ep['inputs']['graph']['path']);inventory=Inventory(graph);text,pins=serialize_subset({'records':kept},epfile,table,w/'design.place',inventory);(w/'seed.route').write_text(text);(w/'bindings.json').write_text(json.dumps(pins)+'\n')
  for p in [epfile,table,src/name/'subset.json',graph]:bindings[str(p)]=sha(p)
  cold=R/f'experiments/aes_mapped_fresh_cold_v2_2026-10-08/{name}'
  coldrows=json.loads((cold.parent/'rows.json').read_text());coldrow=next(x for x in coldrows if x['name']==name);cmd=coldrow['command'];row['command']=cmd
  for f in ['output.route','native.log','design.net.post_routing']:shutil.copyfile(cold/f,w/f);bindings[str(cold/f)]=sha(cold/f)
  row.update(native_exit_code=coldrow['native_exit_code'],native_seconds=coldrow['native_seconds']);log=(w/'native.log').read_text();assert coldrow['native_exit_code']==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
  cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);row.update(cpd_ns=cpd,wirelength=wire)
  a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in physical);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert required==observed and a['overflow_units']==0;(w/'audit.json').write_text(json.dumps(a)+'\n')
  files={str(p):sha(p) for p in w.iterdir() if p.is_file()};canonical=canonical_reload({**row,'files':files,'width':128,'decision':'R'},w,out/(name+'_canonical'),inventory)
  row.update(status='NATIVE_PHYSICAL_PARTITION_AND_CANONICAL_PASS',canonical=canonical,all_queries=len(queries),physical_queries=len(physical),ignored_queries=len(nonphysical),seed_queries=0,withheld_seed_queries=0)
 except Exception as error:row['error']=repr(error)
 row['seconds_excluding_archived_estimator']=time.perf_counter()-start;row['files']={str(p):sha(p) for p in w.rglob('*') if p.is_file()};rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['status'],row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Posthoc physical partition and canonical audit of existing fresh unseeded runs; no new routing and no complete fresh timer claimed.'},indent=2)+'\n');assert all(r['status']=='NATIVE_PHYSICAL_PARTITION_AND_CANONICAL_PASS' for r in rows)
