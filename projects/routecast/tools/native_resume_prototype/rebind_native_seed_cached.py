"""Preserve accepted physical paths under original packed identity for next update."""
import json,os,shutil,subprocess
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from serialize_shared_inventory import serialize
from rebind_native_seed import rebind as original_rebind
from relocate_original_identity_v2 import OriginalIdentityRelocator
ROOT=Path(__file__).resolve().parents[2]
def rebind(ctx,inventory,endpoint,route,source,out,identity_cache):
 if not identity_cache:
  seed,proof=original_rebind(ctx,inventory,endpoint,route,source,out);proof["identity_table_sha256"]=sha(Path(out)/"identity.jsonl");(Path(out)/"receipt.json").write_text(json.dumps(proof,indent=2)+"\n");identity_cache["adapter"]=OriginalIdentityRelocator(endpoint,Path(out)/"identity.jsonl",Path(out)/"receipt.json",ctx.graph);return seed,proof
 endpoint,route,source,out=map(Path,(endpoint,route,source,out));out.mkdir(exist_ok=False);meta=json.loads(endpoint.read_text());place=Path(meta['inputs']['place']['path']);net=Path(meta['inputs']['net']['path']);arch=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
 for f,n in ((source/'design.blif','design.blif'),(place,'design.place'),(net,'design.net')):shutil.copyfile(f,out/n)
 table=out/'identity.jsonl';cmd=[str(identity),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--read_rr_graph',str(ctx.graph),'--route_chan_width','300','--num_workers','1','--seed','1','--check_route','full'];bindings={str(f):sha(f) for f in (endpoint,route,place,net,identity,arch,source/'design.blif')};env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NET_IDENTITY_FILE']=str(table)
 relocation=identity_cache['adapter'].relocate(endpoint,table);code=None;paths=physical_paths(route);f=ctx.fields;slots={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(ctx.n) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};records=[]
 for q in meta['connections']:
  name=meta['net_names'][str(q['net_id'])];ps=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(ps)==1;edges=[f['edge_ids'][slots[u,v,sw]] for (u,_),(v,sw) in zip(ps[0],ps[0][1:])];records.append(dict(q,answer=dict(physical_edge_ids=edges)))
 text,_=serialize(dict(records=records),endpoint,table,out/'design.place',inventory);seed=out/'rebound.route';seed.write_text(text);norm=lambda p:{n:Counter(ps) for n,ps in physical_paths(p).items() if ps};assert norm(seed)==norm(route);assert all(sha(f)==h for f,h in bindings.items());result=dict(bindings=bindings,output_sha256=sha(seed),physical_paths_exact=True,command=cmd,identity_capture_exit_code=code,identity_table_sha256=sha(table),identity_relocation=relocation,native_recapture_performed=False);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return seed,result
