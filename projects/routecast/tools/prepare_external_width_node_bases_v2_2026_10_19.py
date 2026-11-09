"""Three graph-static native node-price admissions; never transfer timing or graph IDs."""
import json,os,shutil,subprocess,resource,time,struct,sys,array,math,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def f32(x):return struct.unpack('<f',struct.pack('<f',float(x)))[0]

def map_prices(capture,frameproof,out):
 frame=read(frameproof);assert all(sha(p)==h for p,h in frame['bindings'].items());graph=Path(frame['graph']);assert sha(graph)==frame['graph_sha256'];table=capture/'work/indexed.tsv';lines=[t.split() for t in table.read_text().splitlines()];assert lines[0]==['G',str(frame['graph_nodes']),'8'];indices={int(t[1]):t for t in lines if t[0]=='I'};assert set(indices)==set(range(8));types={0:'SOURCE',1:'SINK',2:'IPIN',3:'OPIN',4:'CHANX',5:'CHANY'};groups={};counts=Counter();details=[]
 for t in lines:
  if t[0]!='N':continue
  kind,idx,count=map(int,t[1:]);row=indices[idx];key=(types[kind],int(row[2]));assert key not in groups and count>0;base,saved,quad=f32(row[3]),f32(row[4]),f32(row[7]);assert math.isfinite(base) and base>=0 and base==saved and quad==0;exact=Fraction(base);scaled=exact*10**18;price=(scaled.numerator+scaled.denominator-1)//scaled.denominator;assert scaled<=price<scaled+1 and price<2**64;groups[key]=price;counts[key]=count;details.append(dict(node_type=key[0],segment=key[1],index=idx,nodes=count,base_float32_text=row[3],base_bits=f'{int.from_bytes(struct.pack("<f",base),"little"):08x}',exact_numerator=exact.numerator,exact_denominator=exact.denominator,integer_base=price,T_quadratic_zero=True))
 assert len(groups)==8 and sum(counts.values())==frame['graph_nodes'];values=array.array('Q');actual=Counter();stack=[]
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   assert int(x.get('id'))==len(values);seg=x.find('segment');key=(x.get('type'),int(seg.get('segment_id')) if seg is not None else -1);assert key in groups;values.append(groups[key]);actual[key]+=1;parent.remove(x);x.clear()
  if x.tag=='rr_nodes':break
  stack.pop()
 assert actual==counts;target=out/'node_base.u64';target.write_bytes(values.tobytes());reload=array.array('Q');reload.frombytes(target.read_bytes());assert reload==values;native=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_net.cpp';body=native.read_text();assert 'T_quadratic > 0.' in body and 'saved_base_cost * factor' in body and 'factor = sqrt(fanout);' in body;paths=[frameproof,graph,table,capture/'receipt.json',capture/'protocol.json',target,native,Path(__file__).resolve()];proof=out/'verification.json';proof.write_text(json.dumps(dict(schema='ROUTECAST_GRAPH_STATIC_NODE_BASE_V2',status='GRAPH_NATIVE_INDEXED_GROUPS_XML_PRICES_AND_STATIC_FANOUT_VERIFIED',width=frame['width'],graph_sha256=frame['graph_sha256'],nodes=len(values),scale=10**18,array_byteorder=sys.byteorder,groups=details,all_native_base_equal_saved=True,all_native_T_quadratic_zero=True,ceil_error_less_than_one_lattice_unit=True,graph_static_price_scope=True,bindings={str(p):sha(p) for p in paths},scope='Unique native type/indexed-segment groups and full XML node/group counts, not a per-node native getter dump. T_quadratic0/base=saved plus pinned fanout logic admits static prices for this graph. Source nonzero price preserved; model must explicitly exclude structural root. No physical delay/STA, budget, forecast or strict-family claim.'),indent=2));return proof,len(values),sorted(set(values))

def main():
 out=R/'experiments/prospective_external_family_width_node_bases_v2_2026-10-19';out.mkdir(exist_ok=False);matrix=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/verification.json';m=read(matrix);assert all(sha(p)==h for p,h in m['bindings'].items());frames={r['width']:Path(r['frame_verification']) for r in m['rows'] if r['frame']=='source'};old=R/'experiments/prospective_external_family_initialized_node_base_v1_2026-10-19';template=read(old/'protocol.json');build=R/'build/native_indexed_cost_dump_v1_2026-10-10';br=read(build/'receipt.json');binary=build/'sequence_vpr';assert sha(binary)==br['binary_sha256'] and all(sha(p)==h for p,h in br['bindings'].items()) and all(sha(p)==h for p,h in br['source_sha256'].items());jobs=[]
 for w in [96,128,160]:
  frame=read(frames[w]);cmd=list(template['command']);cmd[0]=str(binary);cmd[cmd.index('--read_rr_graph')+1]=frame['graph'];cmd[cmd.index('--route_chan_width')+1]=str(w);jobs.append(dict(width=w,frame_verification=str(frames[w]),reuse_existing_source128=w==128,command=None if w==128 else cmd))
 paths=[matrix,old/'verification.json',build/'receipt.json',binary,Path(__file__).resolve()];bindings={str(p):sha(p) for p in paths};(out/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,policy='Two fresh graph96/160 initialized indexed dumps; source128 capture reused with paid provenance. Native exits before routing, no criticality substitution. Prices admitted per exact graph and common integer lattice, all role/width cases retained.'),indent=2));rows=[]
 for job in jobs:
  w=job['width'];frameproof=frames[w];frame=read(frameproof);e=read(Path(frame['endpoint']));d=out/f'w{w:03d}';d.mkdir();tick=time.perf_counter()
  if w==128:
   capture=old;assert read(old/'verification.json')['graph_sha256']==frame['graph_sha256'];assert all(sha(p)==h for p,h in read(old/'verification.json')['bindings'].items())
  else:
   capture=d/'capture';capture.mkdir();work=capture/'work';work.mkdir();pre={str(p):sha(p) for p in [frameproof,Path(frame['graph']),binary,build/'receipt.json']}
   for src,name in [(Path(e['inputs']['net']['path']),'design.net'),(Path(e['inputs']['place']['path']),'design.place'),(old/'work/design.blif','design.blif')]:shutil.copyfile(src,work/name);assert sha(src)==sha(work/name);pre.update({str(p):sha(p) for p in [src,work/name]})
   env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_INDEXED_COST_DUMP']=str(work/'indexed.tsv');(capture/'protocol.json').write_text(json.dumps(dict(command=job['command'],bindings=pre,environment_set={'ROUTECAST_INDEXED_COST_DUMP':str(work/'indexed.tsv')},phase='Read-only native indexed dump after initialization, clean exit before routing.'),indent=2));start=time.perf_counter()
   def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
   with (work/'native.log').open('x') as log:r=subprocess.run(job['command'],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
   passed=r.returncode==0 and 'ROUTECAST indexed cost metadata exported before routing' in (work/'native.log').read_text() and not list(work.glob('*.route'));assert all(sha(p)==h for p,h in pre.items());(capture/'receipt.json').write_text(json.dumps(dict(passed=passed,exit_code=r.returncode,process_seconds=time.perf_counter()-start,bindings={str(p):sha(p) for p in [capture/'protocol.json',work/'indexed.tsv',work/'native.log']}),indent=2));assert passed
  proof,n,prices=map_prices(capture,frameproof,d);rows.append(dict(width=w,graph_sha256=frame['graph_sha256'],nodes=n,verification=str(proof),verification_sha256=sha(proof),capture_directory=str(capture),reused_paid_capture=w==128,price_values=prices,capture_and_mapping_component_seconds=time.perf_counter()-tick));(out/'progress.json').write_text(json.dumps(dict(rows=rows),indent=2));print('WIDTH_NODE_BASE_VERIFIED',w,n,prices,'reused',w==128,flush=True)
 assert len(rows)==3 and all(sha(p)==h for p,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(status='ALL3_GRAPH_STATIC_NODE_BASE_DOMAINS_FLOAT32_CEIL_AND_FANOUT_PROOFS_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [out/'protocol.json',*[Path(r['verification']) for r in rows]]},fresh_captures=2,reused_paid_capture=1,strict_unseen_admitted=False,new_native_route_labels=False,scope='Static graph-affine soft-price inputs only. Source timing capture epochs are distinct obligations; no source timing copied into targets.'),indent=2))
if __name__=='__main__':main()
