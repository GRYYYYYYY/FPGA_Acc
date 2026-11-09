"""Independent Fraction/f32 numeric reference, including rounding and domain failures."""
import json,struct,random,hashlib,math,time
from pathlib import Path
from fractions import Fraction as F
from compiled_map_materialize_v2 import materialize,BINARY
from bound_allnet_map_query_v2 import Query
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'map_materialize_contract_v2_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def val(bits):return struct.unpack('>f',bytes.fromhex(bits))[0]
def ref(data,allowed,terminal,bits,scale,q):
 c=val(bits)
 if not math.isfinite(c) or not 0<=c<=1:raise ValueError('c')
 out=[]
 for (zero,one),ok,term in zip(struct.iter_unpack('<ff',data),allowed,terminal):
  if not ok:out.append(0);continue
  if any(not math.isfinite(v) or v<0 for v in [zero,one]):raise ValueError('native')
  if term:
   if zero!=one:raise ValueError('terminal')
   h=zero
  else:h=f32(f32(c*one)+f32(f32(1-c)*zero))
  v=F.from_float(f32(f32(1.2)*h))*scale*q;h=-(-v.numerator//v.denominator)
  if h>=2**128:raise ValueError('overflow')
  out.append(h)
 return tuple(out)
def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020517);fixtures=0;rejects=0;nodes=0
 for k in range(500):
  n=32;term=[rng.randrange(2) for _ in range(n)];allowed=[rng.randrange(2) for _ in range(n)];pairs=[]
  for t in term:
   a=struct.unpack('<f',struct.pack('<I',rng.randrange(0x7f800000)))[0];b=a if t else struct.unpack('<f',struct.pack('<I',rng.randrange(0x7f800000)))[0];pairs.append((a,b))
  data=b''.join(struct.pack('<ff',*x) for x in pairs);bits=struct.pack('>I',rng.randrange(0x3f800001)).hex();scale=rng.randrange(1,2**64);q=rng.randrange(1,2**64)
  try:expected=ref(data,allowed,term,bits,scale,q)
  except (ValueError,OverflowError):
   try:materialize(data,allowed,term,bits,scale,q)
   except ValueError:rejects+=1
   else:raise AssertionError('invalid accepted')
  else:assert materialize(data,allowed,term,bits,scale,q)==expected;fixtures+=1;nodes+=n
 # Explicit valid subnormal/rounding/large denominator vectors, avoid whole-fixture overflow.
 for bits in ['00000000','00000001','3eaaaaab','3f000000','3f800000']:
  data=b''.join(struct.pack('<II',a,b) for a,b in [(0,0),(1,2),(0x00800000,1),(0x30800000,0x31000000),(0x3f800000,0x3f800001)])
  for q in [1,2**24,2**64-1]:assert materialize(data,[1]*5,[0]*5,bits,10**18,q)==ref(data,[1]*5,[0]*5,bits,10**18,q);fixtures+=1;nodes+=5
 p=E/'wbuart_allnet_map_preflight_v1_2026-10-20';m=json.loads((p/'manifest.json').read_text());c=m['cases'][1];timing=E/'wbuart_frame_timings_v1_2026-10-20/w096/episode_01/initial_connection_criticalities.json';digest=json.loads((p/'adapter_verification_v1.json').read_text())['payload_sha256'];query=Query(p/'on/allmap.bin',c['endpoint'],timing,digest);rows=[]
 for t in [x for x in json.loads(timing.read_text()) if x['native_net_id']==0]:
  cid=t['connection_id'];source,target=query.connections[cid];allowed=[k in ['CHANX','CHANY','IPIN','SINK'] or n==source or n in query.exits[source] for n,k in enumerate(query.kinds)];term=[k in ['IPIN','SINK'] for k in query.kinds];offset=query.offset+query.targets[target]*query.n*8;data=query.data[offset:offset+query.n*8];bits=t['criticality_bits'];q=F.from_float(val(bits)).denominator;start=time.perf_counter();expected=ref(data,allowed,term,bits,10**18,q);python_seconds=time.perf_counter()-start;start=time.perf_counter();actual=materialize(data,allowed,term,bits,10**18,q);cpp_seconds=time.perf_counter()-start;assert actual==expected;rows.append({'CID':cid,'nodes':query.n,'python_seconds':python_seconds,'cpp_adapter_seconds':cpp_seconds});nodes+=query.n
 query.close();files=[Path(__file__),R/'tools/compiled_map_materialize_v2.py',BINARY,R/'build/map_priority_materialize_v2_2026-10-20/receipt.json',p/'adapter_verification_v1.json'];(D/'verification.json').write_text(json.dumps({'status':'STANDALONE_STAGED_F32_CEIL_WORDS_MATCH_REFERENCE_NOT_IN_BATCH','valid_random_and_edge_fixtures':fixtures,'invalid_random_rejections':rejects,'nodes_in_valid_fixtures':nodes,'real_rows':rows,'bindings':{str(p):sha(p) for p in files},'scope':'Standalone numerical/performance evidence; not integrated in running frozen experiment. No full-model parity or end-to-end speedup claim.'},indent=2)+'\n');print('MATERIALIZER_CONTRACT_PASS',fixtures,rejects,rows)
if __name__=='__main__':main()
