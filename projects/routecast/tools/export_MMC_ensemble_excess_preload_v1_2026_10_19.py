"""Input-only native excess-cost artifact; no VPR preload hook yet."""
import pathlib,json,hashlib,struct,math,xml.etree.ElementTree as ET
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';ap=M/'independent_prediction_verification_v1.json';a=json.loads(ap.read_text());assert a['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';spec=json.loads((M/'protocol.json').read_text());graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==spec['bindings'][str(graph)];O=R/'experiments/mmc_ensemble_excess_preload_v1_2026-10-19';O.mkdir();caps={};node_count=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==node_count;node_count+=1
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:caps[int(e.get('id'))]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert node_count==904438 and len(caps)==258720;bindings={str(p):sha(p) for p in [graph,ap,M/'protocol.json',pathlib.Path(__file__).resolve()]};rows=[]
 def emit(path,entries):
  with path.open('x') as f:
   f.write(f'RCRISK1 {sha(graph)} {node_count} {len(entries)}\n')
   for n,bits in entries:f.write(f'{n} {bits}\n')
  words=path.read_text().splitlines();assert len(words)==len(entries)+1
  assert words[0].split()==['RCRISK1',sha(graph),str(node_count),str(len(entries))]
  seen=set()
  for line,(n,bits) in zip(words[1:],entries):
   assert list(map(int,line.split()))==[n,bits] and n in caps and n not in seen;seen.add(n);value=struct.unpack('<f',struct.pack('<I',bits))[0];assert math.isfinite(value) and value>=0
  bindings[str(path)]=sha(path)
 emit(O/'zero.risk',[])
 for case in spec['cases']:
  p=M/case/'expected_unique_NET_occupancy.json';assert a['bindings'][str(p)]==sha(p);ledger={int(n):Fraction(x) for n,x in json.loads(p.read_text()).items()};entries=[];maxerror=Fraction(0);underflow=0
  for n,capacity in sorted(caps.items()):
   excess=max(Fraction(0),ledger.get(n,0)-capacity)
   if not excess:continue
   packed=struct.pack('<f',float(excess));value=struct.unpack('<f',packed)[0];bits=struct.unpack('<I',packed)[0];assert math.isfinite(value) and value>=0;maxerror=max(maxerror,abs(Fraction.from_float(value)-excess))
   if value==0:underflow+=1
   else:entries.append((n,bits))
  emit(O/(case+'.risk'),entries);bindings[str(p)]=sha(p);rows.append(dict(case=case,positive_excess_channels=len(entries),positive_underflow_channels=underflow,max_absolute_binary32_conversion_error=str(maxerror)));print('EXCESS INPUT',case,len(entries),flush=True)
 with (O/'verification.json').open('x') as f:json.dump(dict(status='THREE_BOUND_GRAPH_EXCESS_PRELOAD_INPUTS_AND_ZERO_CONTROL_VERIFIED',bindings=bindings,rows=rows,format='RCRISK1 graphSHA nodeCount entryCount; sorted unique RRid and IEEE754binary32 excess bits as decimal integers',mapping='max(0,expected_unique_NET_demand-capacity), CHAN only. Proposed native initial acc_cost=1+router_opts.acc_fac*excess, one pseudo-iteration; no fitted scale or outcome-specific choice.',native_hook_implemented=False,zero_native_equivalence_pending=True,native_jobs_launched=0,original_final_occupancy_gate_still_failed=True,scope='Preload input export/roundtrip only. Not probability calibration, actual native pathfinder use, legality, quality, STA or complete-time gain. Independent native loader and zero-input equivalence required before comparison.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
