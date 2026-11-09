"""Public driver/RR/sink decomposition, invariance and exact float32 edge reconstruction."""
import json,csv,hashlib,struct,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_delay_components_v1_2026-10-19';OLD=E/'prospective_external_family_delay_perturbations_v1_2026-10-19';BASE=E/'prospective_external_family_clock_constraints_v1_2026-10-19';MAP=E/'prospective_external_family_current_timing_graph_v1_2026-10-19';B=R/'build/native_external_delay_components_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def f32(v):return struct.unpack('f',struct.pack('f',float(v)))[0]
def bits(v):return struct.pack('>f',float(v)).hex()
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def components(p):
 result=defaultdict(dict)
 for r in table(p):
  key=int(r['edge']),r['mode'];index=int(r['component']);assert index not in result[key];result[key][index]=(r['type'],f32(r['delay_s']))
 return result

def main():
 p=read(D/'protocol.json');assert all(sha(k)==h for k,h in p['bindings'].items());prior=read(OLD/'verification_v2.json');assert prior['passed'] and all(sha(k)==h for k,h in prior['bindings'].items());t=read(D/'terminal.json');assert len(t['rows'])==9 and all(r['exit_code']==0 and r['marker'] and r['no_route_generated'] and r['initial_connection_bytes_equal'] for r in t['rows']);bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'terminal.json'):sha(D/'terminal.json'),str(OLD/'verification_v2.json'):sha(OLD/'verification_v2.json'),str(B/'sequence_vpr'):sha(B/'sequence_vpr'),str(Path(__file__).resolve()):sha(__file__)};results=[];prehash={}
 for r in t['rows']:
  case,mode=r['case'].rsplit('/',1);out=D/r['case'];old=OLD/r['case'];base=BASE/case
  for name in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','clock_constraints.tsv','initial_connections.tsv','updated_connections.tsv','delay_changes.tsv']:
   assert sha(out/name)==sha(old/name);bindings[str(out/name)]=sha(out/name);bindings[str(old/name)]=sha(old/name)
  before=components(out/'components_before.tsv');after=components(out/'components_after.tsv');mapping=read(MAP/case/'external_edge_CID_bindings_v1.json');edges0={int(e['edge']):e for e in table(base/'timing_edges.tsv')};edges1={int(e['edge']):e for e in table(out/'timing_edges.tsv')};rr0={(int(q['net']),int(q['pin'])):q for q in table(out/'initial_connections.tsv')};rr1={(int(q['net']),int(q['pin'])):q for q in table(out/'updated_connections.tsv')};count=0
  for q in mapping:
   eid=q['edge'];pin=q['native_net_id'],q['local_sink_pin']
   for kind,col in [('MAX','value_max_or_setup_s'),('MIN','value_min_or_hold_s')]:
    a,b=before[eid,kind],after[eid,kind];assert set(a)==set(b)=={0,1,2};assert a[1][0]==b[1][0]=='inter-block routing';assert all(math.isfinite(c[1]) and c[1]>=0 for c in a.values());assert bits(a[0][1])==bits(b[0][1]) and bits(a[2][1])==bits(b[2][1]);assert bits(a[1][1])==bits(rr0[pin]['delay_s']) and bits(b[1][1])==bits(rr1[pin]['delay_s'])
    for comp,edge in [(a,edges0[eid]),(b,edges1[eid])]:
     combined=f32(f32(comp[0][1]+comp[1][1])+comp[2][1]);assert bits(combined)==bits(edge[col]);count+=1
  h=sha(out/'components_before.tsv')
  if case in prehash:assert prehash[case]==h
  prehash[case]=h;results.append(dict(case=case,mode=mode,mapped_edges=len(mapping),driver_sink_MAX_MIN_components_bitwise_invariant=True,native_RR_component_matches_delay_matrix=True,exact_component_reconstruction_checks=count,original_nine_snapshot_outputs_byte_identical=True));print(json.dumps(results[-1]),flush=True)
  for name in ['components_before.tsv','components_after.tsv']:fp=out/name;bindings[str(fp)]=sha(fp)
  fp=MAP/case/'external_edge_CID_bindings_v1.json';bindings[str(fp)]=sha(fp);fp=base/'timing_edges.tsv';bindings[str(fp)]=sha(fp)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL9_PUBLIC_COMPONENTS_INVARIANT_AND_816732_FLOAT32_EDGE_RECONSTRUCTIONS_EXACT',rows=results,bindings=bindings,scope='Public AGGREGATED resolver, no private header/vtable/source modifications. Current nominal packed mapping and synthetic data delays only. Internal components invariant over these delay changes, not proved invariant after different physical IPIN assignment/packed pin swap or placement move. No quality/full timing acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
