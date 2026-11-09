"""Prospective priority encoder family functional/input/policy freeze."""
import ast,json,random,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/priority_family_freeze_2026-10-07'
def generate(width,lanes):
 lines=['.model priority_encoder','.inputs '+' '.join(f'x{l}_{b}' for l in range(lanes) for b in range(width)),'.outputs '+' '.join(f'valid{l} idx{l}_{b}' if b==0 else f'idx{l}_{b}' for l in range(lanes) for b in range(width.bit_length()-1))];gates=[];serial=0
 def gate(args,patterns):
  nonlocal serial
  name=f'g{serial}';serial+=1;lines.append('.names '+' '.join([*args,name]));lines.extend(p+' 1' for p in patterns);gates.append((args,name,patterns));return name
 for lane in range(lanes):
  level=[(f'x{lane}_{b}',[]) for b in range(width)]
  while len(level)>1:
   new=[]
   for i in range(0,len(level),2):
    lo,li=level[i];hi,hj=level[i+1];valid=gate([lo,hi],['1-','-1']);index=[gate([hi,a,b],['01-','1-1']) for a,b in zip(li,hj)]+[hi];new.append((valid,index))
   level=new
  valid,index=level[0]
  for source,name in [(valid,f'valid{lane}')]+[(s,f'idx{lane}_{b}') for b,s in enumerate(index)]:lines.extend([f'.names {source} {name}','1 1']);gates.append(([source],name,['1']))
 lines.append('.end');return '\n'.join(lines)+'\n',gates

def check(width,lanes,vectors):
 text,gates=generate(width,lanes)
 for words in vectors:
  v={f'x{l}_{b}':(word>>b)&1 for l,word in enumerate(words) for b in range(width)}
  for args,name,patterns in gates:v[name]=int(any(all(c=='-' or int(c)==v[a] for c,a in zip(pattern,args)) for pattern in patterns))
  for l,word in enumerate(words):
   assert v[f'valid{l}']==int(word!=0);actual=sum(v[f'idx{l}_{b}']<<b for b in range(width.bit_length()-1));assert actual==max(0,word.bit_length()-1)
 return text

def closure(seeds):
 found={};todo=list(seeds)
 while todo:
  p=todo.pop()
  if p in found:continue
  found[p]=sha(p);tree=ast.parse(p.read_text())
  for node in ast.walk(tree):
   names=[node.module] if isinstance(node,ast.ImportFrom) and node.level==0 else [x.name for x in node.names] if isinstance(node,ast.Import) else []
   for name in names:
    if name:
     f=ROOT/'tools'/(name.split('.')[0]+'.py')
     if f.exists() and f not in found:todo.append(f)
 return {str(k):v for k,v in found.items()}
if __name__=='__main__':
 OUT.mkdir();a=json.loads((ROOT/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());abc=Path(a['yosys_path']).parent.parent/'abc/abc';binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so'
 sources=closure([Path(__file__),ROOT/'tools/predict_priority_frozen.py',ROOT/'tools/pre_route_endpoints.py',ROOT/'tools/immutable_xml_prediction_audit.py',ROOT/'tools/stream_native_route_audit.py']);sources[str(binary)]=sha(binary);sources[str(binary.with_suffix('.cpp'))]=sha(binary.with_suffix('.cpp'))
 protocol=dict(family='balanced unsigned highest-set-bit priority encoder',widths=[32,64,128],lanes=8,sources_sha256=sources,abc_sha256=sha(abc),policy=dict(weight_ns='1/20',connection_cap_ns=1,max_labels=10000,fallback_limit=0,max_whole_net_releases=4,net_order='ascending NET/CID',seed=1,workers=1,channel_width=128,max_router_iterations=100,timeout_s=180),metrics=dict(spatial_bins='layer,x,y,orientation,segment',universe='all positive-capacity channel bins, include zeros',k=20,ties='deterministic lexicographic',incomplete='retain failure and null complete metrics'),split='New family held out from development; no labels yet, all variants retained, no outcome retuning. No universal external corpus claim.',scope='Frontend/predictor transitive local Python sources and private search binary frozen BEFORE any newfamily native run. Native evaluator orchestration and native binaries must also be bound before generating labels; complete heldout evidence pending.')
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');check(8,1,[[i] for i in range(256)]);rng=random.Random(7);rows=[]
 for width in protocol['widths']:
  vectors=[[0]*8,[(1<<width)-1]*8]+[[1<<i]*8 for i in range(width)]+[[rng.getrandbits(width) for _ in range(8)] for _ in range(256)];text=check(width,8,vectors);work=OUT/f'n{width}';work.mkdir();raw=work/'generated.blif';raw.write_text(text)
  for name,cmd in [('map',f'read_blif {raw.resolve()}; strash; if -K 6; write_blif design.blif'),('cec',f'cec {raw.resolve()} design.blif')]:
   with (work/(name+'.log')).open('w') as f:code=subprocess.run([str(abc),'-c',cmd],cwd=work,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
   assert code==0
  assert 'Networks are equivalent' in (work/'cec.log').read_text();sizes=[len(x.split())-2 for x in (work/'design.blif').read_text().splitlines() if x.startswith('.names ')];assert max(sizes)<=6
  rows.append(dict(width=width,oracle_vectors=len(vectors),mapped_luts=len(sizes),files={str(f):sha(f) for f in work.iterdir() if f.is_file()}));print(width,len(sizes),flush=True)
 assert all(sha(f)==d for f,d in sources.items());(OUT/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(OUT/'protocol.json'),rows=rows,exhaustive_small_vectors=256,native_started=False,scope='Independent Python bit_length oracle on all8bit vectors and boundary/sampled actual variants; ABC CEC generated-to-mapped. Not exhaustive full-width specification proof.'),indent=2)+'\n')
