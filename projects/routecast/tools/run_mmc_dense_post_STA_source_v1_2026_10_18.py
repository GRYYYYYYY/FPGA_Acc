"""Exactly one original-source post-STA observation; preserve all parity failures."""
import json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from audit_mmc_v16_native_iteration_work_v1 import parse

def main():
 E=R/'experiments';out=E/'mmc_dense_post_STA_source_v1_2026-10-18';out.mkdir(exist_ok=False);bdir=R/'build/dense_post_STA_source_v1_2026-10-18';bp=bdir/'receipt.json';b=json.loads(bp.read_text());assert b['original_source_recovered_exactly'] and all(sha(k)==h for k,h in b['bindings'].items()) and sha(bdir/'sequence_vpr')==b['binary_sha256'];sp=E/'mmc_dense_post_STA_source_protocol_v1_2026-10-18/protocol.json';spec=json.loads(sp.read_text());assert all(sha(k)==h for k,h in spec['bindings'].items());old=E/'ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/native/mmc';rp=old/'receipt.json';ref=json.loads(rp.read_text());geo=E/'mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(geo.read_text());assert g['bindings'][str(rp)]==sha(rp) and g['bindings'][str(old/'output.route')]==sha(old/'output.route');bindings={**closure([Path(__file__)]),**b['bindings'],str(bp):sha(bp),str(sp):sha(sp),str(rp):sha(rp),str(geo):sha(geo),str(bdir/'sequence_vpr'):sha(bdir/'sequence_vpr')}
 for name in ['design.blif','design.net','design.place']:
  source=old/name;assert sha(source)==ref['files'][str(source)];shutil.copyfile(source,out/name);assert sha(out/name)==sha(source);bindings[str(source)]=sha(source)
 manifest=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';bindings[str(manifest)]=sha(manifest);cmd=ref['command'].copy();cmd[0]=str(bdir/'sequence_vpr');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_DENSE_POST_STA']=str(out/'context.tsv');env['ROUTECAST_DENSE_POST_STA_MANIFEST']=str(manifest);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,reference_directory=str(old),source_only=True,environment_policy='Remove inherited ROUTECAST_ variables; set only the two declared dense read-only capture paths.',dense_capture=env['ROUTECAST_DENSE_POST_STA'],scope='Data acquisition only, original source layout. No target label/candidate policy or speed claim.'),indent=2));tick=time.perf_counter()
 with (out/'native.log').open('x') as log:
  child=subprocess.Popen(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT);stat=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split();(out/'live_process.json').write_text(json.dumps(dict(pid=child.pid,startticks=stat[19],command=cmd),indent=2));code=child.wait()
 elapsed=time.perf_counter()-tick;route=out/'output.route';same=code==0 and route.exists() and route.read_bytes()==(old/'output.route').read_bytes();workequal=False;work=None
 if code==0:
  a=parse((old/'native.log').read_text());work=parse((out/'native.log').read_text());fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes'];workequal=a['iterations']==work['iterations'] and all({k:x[k] for k in fields}=={k:y[k] for k in fields} for x,y in zip(a['rows'],work['rows']))
 assert all(sha(k)==h for k,h in bindings.items());receipt=dict(bindings=bindings,exit_status=code,native_capture_process_seconds=elapsed,route_bytes_equal_reference=same,all_integer_iteration_work_equal_reference=workequal,native_work=work,context_exists=(out/'context.tsv').exists(),original_source_canonical_reload_gate=False,original_source_zero_counter_gate=False,files={str(p):sha(p) for p in out.iterdir() if p.is_file()},scope='One source observation; exact original physical/canonical semantic evidence may transfer only after data/route/phase admission. No original zero-counter gate repair, new forecast or performance gain. All failures/mismatches retained.')
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2));print('DENSE_SOURCE_NATIVE_TERMINAL',code,same,workequal,elapsed,flush=True)
 if not(code==0 and same and workequal and receipt['context_exists']):raise SystemExit(1)
if __name__=='__main__':main()
