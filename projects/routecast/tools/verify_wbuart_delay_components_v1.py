"""All synthetic vectors, exact native float32 component reconstruction and invariance."""
import hashlib,json,csv,math,struct
from pathlib import Path
from verify_external_delay_components_v1 import components
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_delay_components_v1_2026-10-20';BASE=R/'experiments/wbuart_nominal_contexts_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def f32(v):return struct.unpack('<f',struct.pack('<f',float(v)))[0]
def bits(v):return struct.pack('>f',float(v)).hex()
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def main():
 terminal=read(D/'terminal.json');proto=read(D/'protocol.json');assert len(terminal['rows'])==36 and all(r['passed'] for r in terminal['rows'])
 for n,h in proto['bindings'].items():assert sha(Path(n))==h
 mp=BASE/'edge_CID_verification_v1.json';mappingproof=read(mp)
 for n,h in mappingproof['bindings'].items():assert sha(Path(n))==h
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/verify_external_delay_components_v1.py',D/'terminal.json',D/'protocol.json',mp]};rows=[];prehash={};total=0
 for job in proto['jobs']:
  d=D/job['case'];base=BASE/job['base_case'];receipt=read(d/'receipt.json');assert receipt['capture_passed'] and receipt['exit_status']==0
  for n,h in receipt['bindings'].items():assert sha(Path(n))==h
  for n in ['timing_nodes.tsv','clock_constraints.tsv','initial_connections.tsv']:assert sha(d/n)==sha(base/n)
  before=components(d/'components_before.tsv');after=components(d/'components_after.tsv');mapping=read(base/'external_edge_CID_bindings_v1.json');assert len(mapping)==3892 and len({q['connection_id'] for q in mapping})==2493
  edges0={int(e['edge']):e for e in table(base/'timing_edges.tsv')};edges1={int(e['edge']):e for e in table(d/'timing_edges.tsv')};assert set(edges0)==set(edges1)
  rr0={(int(q['net']),int(q['pin'])):q for q in table(d/'initial_connections.tsv')};rr1={(int(q['net']),int(q['pin'])):q for q in table(d/'updated_connections.tsv')};changes={(int(q['net']),int(q['pin'])):q for q in table(d/'delay_changes.tsv')};assert len(rr0)==2493 and set(rr0)==set(rr1)==set(changes)
  for key,q in rr0.items():
   v=f32(q['delay_s']);expected=v
   if job['mode']=='scaled':expected=f32(v*1.25)
   elif job['mode']=='sparse_plus' and key[0]%17==0:expected=f32(v+f32(0.25e-9))
   elif job['mode']=='sparse_zero' and key[0]%29==0:expected=0.
   assert bits(changes[key]['before_s'])==bits(v) and bits(changes[key]['after_s'])==bits(expected)==bits(rr1[key]['delay_s'])
  mapped=set();count=0
  for q in mapping:
   eid=q['edge'];mapped.add(eid);pin=q['native_net_id'],q['local_sink_pin']
   for mode,col in [('MAX','value_max_or_setup_s'),('MIN','value_min_or_hold_s')]:
    a,b=before[eid,mode],after[eid,mode];assert set(a)==set(b)=={0,1,2} and a[1][0]==b[1][0]=='inter-block routing';assert all(math.isfinite(c[1]) and c[1]>=0 for c in [*a.values(),*b.values()]);assert bits(a[0][1])==bits(b[0][1]) and bits(a[2][1])==bits(b[2][1]);assert bits(a[1][1])==bits(rr0[pin]['delay_s']) and bits(b[1][1])==bits(rr1[pin]['delay_s'])
    for parts,edge in [(a,edges0[eid]),(b,edges1[eid])]:assert bits(f32(f32(parts[0][1]+parts[1][1])+parts[2][1]))==bits(edge[col]);count+=1
  for eid,e in edges0.items():
   assert all(e[k]==edges1[eid][k] for k in ['source','sink','type','disabled'])
   if eid not in mapped:assert all(bits(e[col])==bits(edges1[eid][col]) for col in ['value_max_or_setup_s','value_min_or_hold_s'])
  case=job['base_case'];h=sha(d/'components_before.tsv')
  if case in prehash:assert prehash[case]==h
  prehash[case]=h;total+=count;paths=[d/'receipt.json',d/'components_before.tsv',d/'components_after.tsv',d/'updated_connections.tsv',d/'delay_changes.tsv',d/'timing_edges.tsv',base/'timing_edges.tsv',base/'external_edge_CID_bindings_v1.json'];record={'case':case,'mode':job['mode'],'mapped_edges':3892,'routed_CIDs':2493,'exact_component_float32_reconstructions':count,'driver_sink_MAX_MIN_bitwise_invariant':True,'unmapped_edge_weights_bitwise_invariant':True,'all_graph_topology_and_constraints_unchanged':True,'all_native_RR_perturbations_verified':True,'bindings':{str(p):sha(p) for p in paths}};vp=d/'components_verification_v1.json';vp.write_text(json.dumps(record,indent=2)+'\n');rows.append({'case':case,'mode':job['mode'],'verification':str(vp),'sha256':sha(vp),'checks':count});print('WBUART_COMPONENTS_VERIFIED',case,job['mode'],count,flush=True)
 assert len(rows)==36 and total==560448
 for n,h in bindings.items():assert sha(Path(n))==h
 out={'status':'ALL36_NATIVE_PERTURBATION_COMPONENTS_AND560448_FLOAT32_RECONSTRUCTIONS_EXACT','rows':rows,'checks':total,'new_target_route_labels':False,'constant_generator_setup_recurrence_qualified':False,'dynamic_fixed_nominal_feedback_qualified':False,'scope':'Fixed current packing and synthetic RR matrix vectors only. Local driver/sink invariance observed for these vectors; not physical IPIN remap, whole original HDL, generic STA, forecast quality or paid-time gain. Constant-generator reference support remains open.','bindings':{**bindings,**{r['verification']:r['sha256'] for r in rows}}};(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
