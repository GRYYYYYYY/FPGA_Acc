"""One fixed replication for each of4existing layouts; never replace old labels."""
import concurrent.futures,json,os,shutil,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';out=E/'mmc_same_binary_cold_repeat_v1_2026-10-18';out.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);tasks=[]
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 oldroot=E/'ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10';old=oldroot/'cold/native/mmc';oldreceipt=load(old/'receipt.json');oldprotocol=load(oldroot/'protocol.json');geo=load(E/'mmc_native_state_geometry_v1_2026-10-18/protocol.json');assert geo['bindings'][str(old/'receipt.json')]==sha(old/'receipt.json') and geo['bindings'][str(old/'output.route')]==sha(old/'output.route');reference=[('source',old,oldreceipt['command'],oldreceipt['files'],oldprotocol['bindings'],oldreceipt['bindings'])]
 for case in ['case_01','case_02','case_03']:
  folder=E/f'mmc_multiplacement_cold_labels_v1_2026-10-18/{case}';p=load(folder/'protocol.json');v=load(folder/'verification.json');assert v['all_native_physical_and_canonical_pass'];physical=load(folder/'cold/physical_audit.json');assert v['bindings'][str(folder/'cold/physical_audit.json')]==sha(folder/'cold/physical_audit.json');cmd=p['commands']['cold'];reference.append((case,folder/'cold',cmd,v['bindings'],p['bindings'],{cmd[cmd.index('--read_rr_graph')+1]:physical['inputs_sha256']['graph']}))
 archive=[]
 for tag,folder in [('source',E/'mmc_manifest_scope_cold_comparator_v1_2026-10-10/native'),('case_01',E/'mmc_partial_firstpass_equivalence_off_v1_2026-10-18/cold'),('case_01',E/'mmc_partial_seed_engine_equivalence_v1_2026-10-18/cold'),('case_01',E/'mmc_partial_firstpass_equivalence_on_v1_2026-10-18/cold')]:
  if tag=='source':
   p=folder/'receipt.json';d=load(p);assert d['exit_code']==0 and d['native_process_seconds']>0;command=d['command'];duration=d['native_process_seconds'];cert=d['files']
  else:
   p=folder.parent/'verification.json';d=load(p);assert d['all_native_physical_and_canonical_pass'];prot=load(folder.parent/'protocol.json');rr=load(folder.parent/'rows.json');row=next(x for x in rr if x['arm']=='cold');assert row['exit_status']==0 and row['native_process_seconds']>0;command=prot['commands']['cold'];duration=row['native_process_seconds'];cert=d['bindings']
  baseline=next(row for row in reference if row[0]==tag);route=folder/'output.route';assert sha(route)==cert[str(route)]==sha(baseline[1]/'output.route');assert all(sha(folder/n)==sha(baseline[1]/n) for n in ['design.blif','design.net','design.place']);archive.append(dict(layout=tag,folder=str(folder),execution_receipt=str(p),native_seconds=duration,route_bytes_equal=True,recorded_binary_path=command[0],same_binary_path_as_reference=command[0]==baseline[2][0],independent_route_storage=(route.stat().st_dev,route.stat().st_ino)!=( (baseline[1]/'output.route').stat().st_dev,(baseline[1]/'output.route').stat().st_ino)));bindings[str(route)]=sha(route)
 (out/'archived_repeat_evidence.json').write_text(json.dumps(dict(rows=archive,limits='These are actual archived executions with unchanged input and route bytes, but the selected cold observers use different binary paths. They do not establish exact-same-binary replication for all4layouts.'),indent=2))
 plan=[]
 for tag,source,cmd,filecert,codecert,graphcert in reference:
  assert '--routecast_seed' not in ' '.join(cmd)
  for p in [Path(cmd[0]),Path(cmd[1])]:assert sha(p)==codecert[str(p)];bindings[str(p)]=sha(p)
  graph=Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==graphcert[str(graph)];bindings[str(graph)]=sha(graph)
  for name in ['design.blif','design.net','design.place','output.route']:
   p=source/name;assert sha(p)==filecert[str(p)];bindings[str(p)]=sha(p)
  plan.append(dict(layout=tag,reference_directory=str(source),command=cmd,reference_route_sha256=sha(source/'output.route')));tasks.append((tag,source,cmd))
 # Freeze every layout, command and comparison before staging or executing any repetition.
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=plan,replications_per_layout=1,parallel_workers=2,selection='All4existing source+target layouts, fixed before any new native results.',purpose='Baseline repeat-variation control only. No candidate policy, tuning, promotion or substitution of original cold labels. Retain every mismatch and failure.',acceptance='Report byte equality, actual exits and process work. Exact routes can transfer existing originalXML/canonical proofs with identical content inputs; any mismatch remains unadmitted until separately audited.',scope='An observed repeat is not a universal determinism theorem or a performance experiment.'),indent=2))
 def run(task):
  tag,source,cmd=task;folder=out/tag;folder.mkdir()
  for name in ['design.blif','design.net','design.place']:shutil.copyfile(source/name,folder/name);assert sha(source/name)==sha(folder/name)
  start=time.perf_counter()
  with (folder/'native.log').open('x') as log:
   child=subprocess.Popen(cmd,cwd=folder,stdout=log,stderr=subprocess.STDOUT)
   (folder/'live_process.json').write_text(json.dumps(dict(pid=child.pid,startticks=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],command=cmd),indent=2));code=child.wait()
  elapsed=time.perf_counter()-start;route=folder/'output.route';same=code==0 and route.exists() and sha(route)==sha(source/'output.route');result=dict(layout=tag,exit_status=code,native_seconds=elapsed,reference_route_sha256=sha(source/'output.route'),repeat_route_sha256=sha(route) if route.exists() else None,route_bytes_equal=same,files={str(p):sha(p) for p in folder.iterdir() if p.is_file() and p.name!='live_process.json'},scope='New baseline replication; timings descriptive unmatched, not utility gain. Original labels remain unchanged.');(folder/'receipt.json').write_text(json.dumps(result,indent=2));print('REPEAT_DONE',tag,code,same,elapsed,flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,tasks))
 assert all(sha(p)==h for p,h in bindings.items());(out/'results.json').write_text(json.dumps(dict(status='all4_fixed_baseline_repetitions_terminal',bindings=bindings,cases=results,all4_route_bytes_equal=all(r['route_bytes_equal'] for r in results),all4_exit_zero=all(r['exit_status']==0 for r in results)),indent=2))
if __name__=='__main__':main()
