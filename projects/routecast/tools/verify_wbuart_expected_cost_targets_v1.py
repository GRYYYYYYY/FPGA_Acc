"""Exact target-frame CID/pin binding and sampled native float32 priority audit."""
import json,hashlib,struct,math,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_expected_cost_targets_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def bits(x):return struct.pack('>f',x).hex()
def frombits(x):return struct.unpack('>f',bytes.fromhex(x))[0]
def main():
 p=D/'verification.json';assert read(p)['status']=='ALL9_TARGET_EXPECTED_OBSERVER_PHYSICAL_CANONICAL_TRACE_AND_EXACT_PARITY_PASS';assert all(sha(n)==h for n,h in read(p)['bindings'].items());manifest=read(D/'manifest.json');rows=[];total=0;bindings={str(x):sha(x) for x in [Path(__file__),p,D/'manifest.json']}
 for c in manifest['cases']:
  out=Path(c['output']);ep=read(c['endpoint']);queries={q['connection_id']:q for q in ep['connections']};timing=E/'wbuart_frame_timings_v1_2026-10-20'/c['target_case']/'initial_connection_criticalities.json';meta=read(timing);mapping={(q['native_net_id'],q['local_sink_pin']):q for q in meta};observed=[];contributions=[];stages={};nonzero=0;path=out/'expected_cost.tsv';lines=path.read_text().splitlines();assert lines[0]=='EXPECTED_COST 1'
  for i,line in enumerate(lines[1:]):
   w=line.split();assert len(w)==14 and w[0]=='Q' and w[1] in ['seed','expand'];net,pin,node,target=map(int,w[2:6]);assert net==0;m=mapping[net,pin];q=queries[m['connection_id']];assert target==q['sink']==m['target_rr'] and q['source']==m['source_rr'] and q['full_connection_id']==m['full_connection_id'];cr,pres,up,expected,back,priority,astar,offset=map(frombits,w[6:]);assert all(not math.isnan(x) for x in [cr,pres,up,expected,back,priority,astar,offset]);assert 0<=cr<=1 and pres>=0 and up==0 and astar==f32(1.2) and offset==0;reconstructed=f32(back+f32(astar*max(0.,f32(expected-offset))));assert bits(reconstructed)==w[11];nonzero+=expected>0;stages[w[1]]=stages.get(w[1],0)+1
   if priority>0 and math.isfinite(priority) and math.isfinite(back):contributions.append((priority-back)/priority)
   observed.append({'sample_index':i,'stage':w[1],'connection_id':q['connection_id'],'full_connection_id':q['full_connection_id'],'native_net_id':net,'local_sink_pin':pin,'node':node,'target':target,'criticality_bits':w[6],'pres_factor_bits':w[7],'R_upstream_bits':w[8],'expected_bits':w[9],'backward_bits':w[10],'priority_bits':w[11]})
  assert stages.get('seed',0)>0 and stages.get('expand',0)>0 and nonzero>0;payload=out/'expected_cost_CID_samples_v1.json';assert not payload.exists();payload.write_text(json.dumps(observed)+'\n');total+=len(observed);rows.append({'case':c['target_case'],'samples':len(observed),'nonzero_expected_samples':nonzero,'stages':stages,'sample_CIDs':sorted({r['connection_id'] for r in observed}),'median_fraction_of_priority_from_heuristic_diagnostic':statistics.median(contributions),'actual_float32_priority_reconstruction_exact':True,'CID_fullCID_current_target_native_pin_binding_exact':True});print(rows[-1],flush=True)
  for x in [payload,path,timing,Path(c['endpoint']),out/'verification.json']:bindings[str(x)]=sha(x)
 assert len(rows)==9
 (D/'independent_sample_verification_v1.json').write_text(json.dumps({'status':'ALL9_TARGET_EXPECTED_PRIORITY_FLOAT32_AND_CID_IDENTITY_SAMPLES_VERIFIED','rows':rows,'samples':total,'bindings':bindings,'scope':'FixedNET0 actual samples; per-sample heuristic contribution is descriptive, not search ordering causality or completeness. No independent MAP-value implementation/lower-bound proof, full query-state snapshot, generic model heuristic adapter or quality/gain claim.'},indent=2)+'\n');print('TARGET_EXPECTED_COST_SAMPLES_VERIFIED',total)
if __name__=='__main__':main()
