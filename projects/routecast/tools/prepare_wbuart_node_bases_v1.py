"""Three fresh native graph-static price captures, no cross-family value reuse."""
import hashlib,json,os,resource,shutil,subprocess
from pathlib import Path
from prepare_external_width_node_bases_v2_2026_10_19 import map_prices
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_node_bases_v1_2026-10-20';F=R/'experiments/wbuart_width_frames_v2_2026-10-20';S=R/'experiments/wbuart_development_place_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);build=R/'build/native_indexed_cost_dump_v1_2026-10-10';br=json.loads((build/'receipt.json').read_text());binary=build/'sequence_vpr';assert sha(binary)==br['binary_sha256']
 for d in [br.get('bindings',{}),br.get('source_sha256',{})]:
  for n,h in d.items():assert sha(Path(n))==h
 old=R/'experiments/prospective_external_family_initialized_node_base_v1_2026-10-19/protocol.json';cmd0=json.loads(old.read_text())['command'];bindings={str(p):sha(p) for p in [Path(__file__),build/'receipt.json',binary,old,F/'independent_verification_v1.json',R/'tools/prepare_external_width_node_bases_v2_2026_10_19.py']};save(O/'protocol.json',{'bindings':bindings,'widths':[96,128,160],'policy':'Three fresh graph-native initialized indexed dumps, no cross-family numerical values reused. Exit before native routing, unchanged price mapping and IEEE754 float32 ceil to1e18 lattice. T_quadratic0/base=saved/full XML type/segment counts must be verified before static fanout-price use. No timing epoch substitution or route-label generation.'});rows=[]
 for w in [96,128,160]:
  d=O/f'w{w:03d}';d.mkdir();capture=d/'capture';capture.mkdir();work=capture/'work';work.mkdir();fp=F/f'w{w:03d}/source/verification.json';frame=json.loads(fp.read_text());ep=fp.parent/'routing_endpoints.json';e=json.loads(ep.read_text());frame=dict(frame,graph=e['inputs']['graph']['path']);adapter=d/'frame_metadata.json';save(adapter,frame)
  cmd=cmd0.copy();cmd[0]=str(binary);cmd[cmd.index('--read_rr_graph')+1]=frame['graph'];cmd[cmd.index('--route_chan_width')+1]=str(w);pre={str(p):sha(p) for p in [fp,ep,adapter,Path(frame['graph']),binary]}
  for src,n in [(Path(e['inputs']['net']['path']),'design.net'),(Path(e['inputs']['place']['path']),'design.place'),(S/'design.blif','design.blif')]:shutil.copyfile(src,work/n);assert sha(src)==sha(work/n);pre.update({str(p):sha(p) for p in [src,work/n]})
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INDEXED_COST_DUMP']=str(work/'indexed.tsv');save(capture/'protocol.json',{'command':cmd,'bindings':pre,'environment_set':{'ROUTECAST_INDEXED_COST_DUMP':str(work/'indexed.tsv')}})
  def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  with (work/'native.log').open('x') as f:p=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
  passed=p.returncode==0 and 'ROUTECAST indexed cost metadata exported before routing' in (work/'native.log').read_text() and not list(work.glob('*.route'));assert passed
  for n,h in pre.items():assert sha(Path(n))==h
  save(capture/'receipt.json',{'passed':passed,'exit_code':p.returncode,'bindings':{str(p):sha(p) for p in [capture/'protocol.json',work/'indexed.tsv',work/'native.log']}});proof,n,prices=map_prices(capture,adapter,d);rows.append({'width':w,'graph_sha256':frame['graph_sha256'],'nodes':n,'verification':str(proof),'sha256':sha(proof),'price_values':prices});print('WBUART_NODE_BASE_VERIFIED',w,n,flush=True)
 for n,h in bindings.items():assert sha(Path(n))==h
 save(O/'verification.json',{'status':'ALL3_FRESH_WBUART_GRAPH_NATIVE_NODE_BASE_DOMAINS_VERIFIED','rows':rows,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json'),**{r['verification']:r['sha256'] for r in rows}},'fresh_captures':3,'cross_family_value_imports':0,'new_target_route_labels':False,'strict_unseen_admitted':False})
if __name__=='__main__':main()
