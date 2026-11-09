"""Freeze all-nine separate seeded native reference; preserve original cold gates."""
import json,subprocess,sys,concurrent.futures
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_target_source_restart_reference_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);seedproof=E/'wbuart_target_native_seeds_v1_2026-10-20/verification.json';ind=seedproof.parent/'independent_verification_v1.json';assert read(ind)['status']=='ALL9_TARGET_SEED_SELECTION_SOURCE_BLOCKS_PLACEMENT_GRAPH_AND_ENDPOINTS_VERIFIED';assert all(sha(p)==h for p,h in read(seedproof)['bindings'].items());build=R/'build/wbuart_source_seeded_restart_v1_2026-10-20/receipt.json';b=read(build);assert sha(b['binary'])==b['binary_sha256'];runner=R/'tools/run_wbuart_target_source_restart_case_v1.py';cold=E/'wbuart_native_evaluation_v1_2026-10-20/cold_manifest.json';cases=[];files=[Path(__file__),runner,seedproof,ind,build,Path(b['binary']),cold,E/'wbuart_source_restart_boundaries_v1_2026-10-20/verification.json',E/'wbuart_source_restart_disabled_parity_v1_2026-10-20/verification.json'];bindings={str(p):sha(p) for p in files}
 for old in read(cold)['cases']:
  c=dict(old);s=next(x for x in read(seedproof)['rows'] if x['case']==c['target_case']);n=s['retained_NETs'];pins=s['retained_connections'];c.update(case=c['target_case']+'/source_restart',role='separate_development_source_seeded_restart_reference',output=str(D/c['target_case']),utility_arm='disabled',restart_seed=s['seed'],restart_seed_proof=str(seedproof),expected_load_marker=f'ROUTECAST_SOURCE_RESTART retained={n} missing={1074-n} retained_pins={pins} missing_delay=1e-9');c['command']=list(c['command']);c['command'][0]=b['binary'];cases.append(c)
 mp=D/'manifest.json';mp.write_text(json.dumps({'schema':'WBUART_TARGET_SOURCE_RESTART_REFERENCE_V1','phase':'target_source_restart_reference','native_execution_admitted':True,'cases':cases,'bindings':bindings,'commands':[[sys.executable,str(runner),str(mp),c['case']] for c in cases],'workers':3,'scope':'Independent all-nine source-seeded native restart reference with full physical/canonical/owner trace and initial delay readback. Explicit missingNET1ns estimate, not full native state continuation. Existing cold target labels and failed quality gates unchanged; no existing candidate promotion. No new forecast tuning or mixed native utilities. Full paid dependencies include source routing, seed prep/qualification and all audits; no component clock gain claim.'},indent=2)+'\n');print('ALL9_SEPARATE_NATIVE_SOURCE_RESTART_REFERENCE_FROZEN',flush=True)
 def run(c):
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT)
  row={'case':c['case'],'exit_status':rc,'verification':str(Path(c['output'])/'verification.json')};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
if __name__=='__main__':main()
