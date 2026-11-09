"""Freeze a new local sorting-network family before native or prediction labels."""
import json,random,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/bitonic_family_freeze_2026-10-07'
def generate(count,bits):
 lines=['.model bitonic_sort','.inputs '+' '.join(f'x{i}_{b}' for i in range(count) for b in range(bits)),'.outputs '+' '.join(f'y{i}_{b}' for i in range(count) for b in range(bits))];gates=[];counter=0
 def gate(args,table):
  nonlocal counter
  name=f'g{counter}';counter+=1;lines.append('.names '+' '.join([*args,name]));lines.extend(t+' 1' for t in table);gates.append((args,name,table));return name
 words=[[f'x{i}_{b}' for b in range(bits)] for i in range(count)];k=2
 while k<=count:
  j=k//2
  while j:
   for i in range(count):
    partner=i^j
    if partner<=i:continue
    a,b=words[i],words[partner];equal=gate([],['']);greater=gate([],[])
    for bit in reversed(range(bits)):
     gt=gate([a[bit],b[bit]],['10']);term=gate([equal,gt],['11']);greater=gate([greater,term],['1-','-1']);same=gate([a[bit],b[bit]],['00','11']);equal=gate([equal,same],['11'])
    # ascending comparator chooses smaller at i; descending reverses that.
    sel=greater if (i&k)==0 else gate([greater],['0'])
    words[i]=[gate([sel,u,v],['01-','1-1']) for u,v in zip(a,b)]
    words[partner]=[gate([sel,u,v],['0-1','11-']) for u,v in zip(a,b)]
   j//=2
  k*=2
 for i,word in enumerate(words):
  for bit,value in enumerate(word):lines.extend([f'.names {value} y{i}_{bit}','1 1']);gates.append(([value],f'y{i}_{bit}',['1']))
 lines.append('.end');return '\n'.join(lines)+'\n',gates

def check(count,bits,vectors):
 text,gates=generate(count,bits)
 for words in vectors:
  values={f'x{i}_{b}':(w>>b)&1 for i,w in enumerate(words) for b in range(bits)}
  for args,name,table in gates:
   assert name not in values and all(a in values for a in args)
   values[name]=int(any(all(c=='-' or int(c)==values[a] for c,a in zip(pattern,args)) for pattern in table))
  actual=[sum(values[f'y{i}_{b}']<<b for b in range(bits)) for i in range(count)];assert actual==sorted(words),(words,actual)
 return text
if __name__=='__main__':
 OUT.mkdir();availability=json.loads((ROOT/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json').read_text());yosys=Path(availability['yosys_path']);abc=yosys.parent.parent/'abc/abc';assert abc.exists()
 modules=['owner_union_wire_rc_context_cached.py','prefix_timing_owner_wire_staged_reroute.py','prefix_timing_conflict_branch_core.py','exact_incremental_timing_dag.py','cached_rr_endpoint_context.py','native_route_ledger_import_compact.py']
 protocol=dict(family='local unsigned bitonic sorting network',count=[4,8,16],key_bits=8,generator_sha256=sha(Path(__file__)),abc_sha256=sha(abc),frozen_predictor_sources={n:sha(ROOT/'tools'/n) for n in modules},policy=dict(wire_penalty_ns='1/20',connection_cap_ns=1,max_labels=10000,seed=1,workers=1,channel_width=128,max_router_iterations=100,native_timeout_s=180,prefix_policy='zero-future model gate only when complete timing bindings available, abandon attempted prefix on model excess; otherwise explicitly unavailable'),split='All three counts one new locally generated family; no metric-dependent filtering or tuning. Prospective relative to current frozen policy, not universal unseen claim.',scope='Input/frontend functional closure only. Native physical endpoints/timing binding/prediction/hotspot/finalQoR/fullcost not yet executed.')
 (OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 check(4,2,[[v>>(2*i)&3 for i in range(4)] for v in range(256)])
 rows=[];rng=random.Random(1)
 for count in protocol['count']:
  vectors=[[0]*count,[255]*count,list(range(count)),list(reversed(range(count))),[0 if i%2 else 255 for i in range(count)]]+[[rng.randrange(256) for _ in range(count)] for _ in range(256)]
  text=check(count,8,vectors);work=OUT/f'n{count}';work.mkdir();raw=work/'generated.blif';raw.write_text(text);start=time.perf_counter()
  for name,cmd in [('map',f'read_blif {raw.resolve()}; strash; if -K 6; write_blif design.blif'),('cec',f'cec {raw.resolve()} design.blif')]:
   with (work/(name+'.log')).open('w') as stream:code=subprocess.run([str(abc),'-c',cmd],cwd=work,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
   assert code==0
  assert 'Networks are equivalent' in (work/'cec.log').read_text();sizes=[len(x.split())-2 for x in (work/'design.blif').read_text().splitlines() if x.startswith('.names ')];assert sizes and max(sizes)<=6
  rows.append(dict(count=count,oracle_vectors=len(vectors),mapped_luts=len(sizes),map_cec_seconds=time.perf_counter()-start,files={str(f):sha(f) for f in work.iterdir() if f.is_file()}));print(rows[-1],flush=True)
 assert sha(Path(__file__))==protocol['generator_sha256'];assert all(sha(ROOT/'tools'/n)==h for n,h in protocol['frozen_predictor_sources'].items())
 (OUT/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(OUT/'protocol.json'),rows=rows,small_fixture_exhaustive_vectors=256,oracle_scope='Independent Python numeric sorted oracle: all 4x2-bit inputs plus boundary/seeded8-bit vectors; sampled8-bit correctness, not exhaustiveHDL equivalence. ABC CEC checks generated-to-mapped equivalence, not sorting-spec completeness.',native_started=False),indent=2)+'\n')
