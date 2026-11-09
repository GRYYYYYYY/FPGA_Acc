"""Freeze three existing source full-tree loaded qualification jobs."""
import json,subprocess,sys,concurrent.futures
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_source_restart_loaded_qualification_v1_2026-10-20';B=R/'build/wbuart_source_seeded_restart_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);parity=E/'wbuart_source_restart_disabled_parity_v1_2026-10-20/verification.json';p=json.loads(parity.read_text());assert p['status']=='ALL3_SOURCE_DISABLED_ZERO_PHYSICAL_CANONICAL_TRACE_AND_ORIGINAL_PATH_PARITY_PASS';assert all(sha(n)==h for n,h in p['bindings'].items());b=json.loads((B/'receipt.json').read_text());assert sha(b['binary'])==b['binary_sha256'];source=E/'wbuart_native_sources_v1_2026-10-20/manifest.json';cases=[];runner=R/'tools/run_wbuart_source_restart_case_v1.py';bindings={str(p):sha(p) for p in [Path(__file__),runner,parity,B/'receipt.json',Path(b['binary']),source]}
 for c in json.loads(source.read_text())['cases']:
  c=dict(c);old=Path(c['output']);c.update(case=f"w{c['width']:03d}/source/loaded",output=str(D/f"w{c['width']:03d}"),utility_arm='disabled',restart_seed=str(old/'output.route'),restart_seed_proof=str(old/'verification.json'),graph_nodes=json.loads((E/'wbuart_quality_domains_v1_2026-10-20'/f"w{c['width']:03d}/verification.json").read_text())['graph_nodes']);c['command'][0]=b['binary'];cases.append(c)
  for p in [old/'output.route',old/'verification.json',Path(c['endpoint'])]:bindings[str(p)]=sha(p)
 mp=D/'manifest.json';mp.write_text(json.dumps({'schema':'WBUART_SOURCE_RESTART_QUALIFICATION_V1','phase':'source_qualification','native_execution_admitted':True,'cases':cases,'bindings':bindings,'scope':'All3 existing-source full-tree native load only. Require1074 complete NETs/2493 pins, zero missing trees, full physical/canonical/trace and delay readback. No expected output parity with cold or quality/utility claim. Fixed perpin numeric reconstruction pending, target seed conversion not admitted.'},indent=2)+'\n')
 def run(c):
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT)
  result={'case':c['case'],'exit_status':rc,'verification':str(Path(c['output'])/'verification.json')};print(json.dumps(result),flush=True);return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'rows':rows,'all_pass':all(r['exit_status']==0 for r in rows)},indent=2)+'\n')
if __name__=='__main__':main()
