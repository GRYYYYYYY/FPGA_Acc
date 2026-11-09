"""Float32 actual priority arithmetic and observer-on/off native behavior parity."""
import json,hashlib,struct,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_expected_cost_on_qualification_v1_2026-10-20';OFF=E/'wbuart_expected_cost_off_qualification_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def bits(x):return struct.pack('>f',x).hex()
def frombits(x):return struct.unpack('>f',bytes.fromhex(x))[0]
def main():
 onproof=D/'verification.json';offproof=OFF/'verification.json';assert read(onproof)['status']==read(offproof)['status']=='ALL3_SOURCE_DISABLED_ZERO_PHYSICAL_CANONICAL_TRACE_AND_ORIGINAL_PATH_PARITY_PASS';rows=[];bindings={str(p):sha(p) for p in [Path(__file__),onproof,offproof]};total=0
 for width in [96,128,160]:
  meta=read(E/'wbuart_frame_timings_v1_2026-10-20'/f'w{width:03d}/source/initial_connection_criticalities.json');targets={(r['native_net_id'],r['local_sink_pin']):r['target_rr'] for r in meta}
  for arm in ['disabled','zero']:
   out=D/'native'/f'w{width:03d}'/arm;before=OFF/'native'/f'w{width:03d}'/arm;a,b=read(out/'verification.json'),read(before/'verification.json');assert all(sha(p)==h for p,h in a['bindings'].items());assert all(sha(p)==h for p,h in b['bindings'].items());assert all(a[k]==b[k] for k in ['iterations','wirelength','diagnostic_cpd_ns','native_work']);assert sha(out/'output.route')==sha(before/'output.route') and sha(out/'owner_trace.tsv')==sha(before/'owner_trace.tsv');path=out/'expected_cost.tsv';lines=path.read_text().splitlines();assert lines[0]=='EXPECTED_COST 1';stages={};nonzero=0
   for line in lines[1:]:
    w=line.split();assert len(w)==14 and w[0]=='Q' and w[1] in ['seed','expand'];net,pin,node,target=map(int,w[2:6]);assert net==0 and targets[net,pin]==target;cr,pres,upstream,expected,backward,priority,astar,offset=map(frombits,w[6:]);assert all(not math.isnan(x) for x in [cr,pres,upstream,expected,backward,priority,astar,offset]);assert 0<=cr<=1 and pres>=0 and upstream==0 and astar==f32(1.2) and offset==0;reconstructed=f32(backward+f32(astar*max(0.,f32(expected-offset))));assert bits(reconstructed)==w[11],(line,bits(reconstructed));stages[w[1]]=stages.get(w[1],0)+1;nonzero+=expected>0;total+=1
   assert stages.get('seed',0)>0 and stages.get('expand',0)>0 and nonzero>0;rows.append({'width':width,'arm':arm,'queries':len(lines)-1,'stages':stages,'nonzero_expected_cost_queries':nonzero,'actual_float32_priority_reconstruction_exact':True,'route_owner_trace_work_counters_observer_off_on_equal':True});bindings[str(out/'verification.json')]=sha(out/'verification.json');bindings[str(before/'verification.json')]=sha(before/'verification.json');print(rows[-1],flush=True)
 assert len(rows)==6
 (D/'independent_expected_cost_verification_v1.json').write_text(json.dumps({'status':'ALL6_SOURCE_OBSERVER_PARITY_AND_ACTUAL_EXPECTED_PRIORITY_FLOAT32_SAMPLES_VERIFIED','samples':total,'rows':rows,'bindings':bindings,'scope':'Fixed NET0 actual source-routing expected-cost samples and exact priority formula, no full occupancy/query iteration snapshots, no expected MAP value independent implementation/admissibility proof, no target capture/model heuristic/quality or speed claim.'},indent=2)+'\n');print('EXPECTED_PRIORITY_SAMPLES_VERIFIED',total)
if __name__=='__main__':main()
