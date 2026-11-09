"""Native pres words, exact overuse summaries, dynamic BB and timing domains."""
import json,struct,math,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_resident_phase_trial_v1_2026-10-20'
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def value(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert len(v['rows'])==18 and all(x['all_iteration_snapshots_complete'] and x['all_iteration_summary_fields_match_except_clocks'] and x['final_physical_sequences_identical'] for x in v['rows']);bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};rows=[];total=0
 for row in v['rows']:
  if not row['case'].endswith('/capture'):continue
  case=row['case'].rsplit('/',1)[0];d=D/row['case'];phase=d/'boundary/phase.tsv';lines=[list(map(int,line.split())) for line in phase.read_text().splitlines()];assert len(lines)==row['iterations'];native=(d/'native.log').read_text();assert 'RouterOpts.first_iter_pres_fac: 0.000000' in native and 'RouterOpts.initial_pres_fac: 0.500000' in native and 'RouterOpts.pres_fac_mult: 1.300000' in native;previous=None;pres=0.;rounds=[]
  for i,t in enumerate(lines,1):
   assert len(t)==10 and t[0]==i and t[1]==bits(pres);pres=f32(.5) if i==1 else f32(pres*f32(1.3));rawp=d/'boundary'/f'iteration_{i}.bin';raw=rawp.read_bytes();over=[max(0,occ-cap) for nid,kind,occ,cap,word in struct.iter_unpack('<QIiiI',raw[24:])];assert (t[2],t[3],t[4])==(sum(x>0 for x in over),sum(over),max(over,default=0));timing=list(map(value,t[6:]));assert all(math.isfinite(x) for x in timing);assert timing[0]<=timing[1]<=0 and timing[2]<=timing[3]<=0
   boxp=d/'boundary'/f'boxes_{i}.bin';raw=boxp.read_bytes();assert raw[:8]==b'RCBOX001';ii,n=struct.unpack_from('<QQ',raw,8);assert ii==i and len(raw)==24+32*n;boxes=list(struct.iter_unpack('<Q6i',raw[24:]));assert n==1792
   for idx,(net,xmin,xmax,ymin,ymax,lmin,lmax) in enumerate(boxes):assert idx==net and 0<=xmin<=xmax<=14 and 0<=ymin<=ymax<=14 and lmin==lmax==0
   changed=None if previous is None else sum(a!=b for a,b in zip(previous,boxes));previous=boxes;rounds.append(dict(iteration=i,pres_fac_bits=t[1],pres_fac=value(t[1]),overused_nodes=t[2],overuse_units=t[3],worst_overuse=t[4],native_logged_BB_updated=t[5],actual_boxes_changed_since_previous_boundary=changed,timing_summary_words=t[6:]));total+=1
   for p in [rawp,boxp]:bindings[str(p)]=sha(p)
  p=d/'phase_verification_v1.json';p.write_text(json.dumps(dict(case=case,rows=rounds,scope='BB rows joined only by native array index, no unsupported mapping to endpoint NET IDs. Timing summary words captured from const float getters and checked for finite/sign/ordering, not perpin criticality/STA proof.'),indent=2)+'\n');rows.append(dict(case=case,boundaries=len(rounds),box_change_events=sum((x['actual_boxes_changed_since_previous_boundary'] or 0)>0 for x in rounds),actual_total_NET_box_changes=sum(x['actual_boxes_changed_since_previous_boundary'] or 0 for x in rounds),logged_updated_sum=sum(x['native_logged_BB_updated'] for x in rounds),proof=str(p),sha256=sha(p)));bindings[str(phase)]=sha(phase)
 source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_utils.cpp';s=source.read_text();assert 'std::vector<ParentNetId> out_bb_updated_nets)' in s and 'out_bb_updated_nets.push_back(net);' in s;bindings[str(source)]=sha(source);assert total==227 and all(sha(p)==h for p,h in bindings.items());(D/'phase_verification_v1.json').write_text(json.dumps(dict(rows=rows,boundaries=total,bindings=bindings,finding='Native dynamic_update_bounding_boxes output vector passed by value; actual BB modifications can coexist with zero returned/logged update count. Baseline left unchanged.',scope='Observed phase/pres float32 recurrence, native overuse/occupancy, BB ranges and changes, and four native timing-summary float words. Not full timing/connection state serialization, stop policy, disk restore, generic determinism or fullpaid speedup.'),indent=2)+'\n');print('PHASE_VERIFIED',total,[(r['case'],r['actual_total_NET_box_changes'],r['logged_updated_sum']) for r in rows])
if __name__=='__main__':main()
