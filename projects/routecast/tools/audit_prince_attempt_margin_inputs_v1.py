"""Independent exact-rational certificate of all raw candidate margin minima."""
import json,struct,mmap,math,bisect
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_attempt_scope_competition_v1_2026-10-20';S=E/'prince_search_attempt_trial_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def number(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def ratio(a,b):
 an,ad=number(a).as_integer_ratio();bn,bd=number(b).as_integer_ratio();return an*bd,ad*bn

def main():
 frozen=load(D/'frozen_inputs.json');bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',Path(__file__)]};rows=[];total_records=total_events=0
 for row in frozen['rows']:
  if row['status']!='ACTUAL_SCOPE_AND_MARGIN_INPUTS_FROZEN':continue
  c=row['case'];cut=row['ready_iteration'];src=S/c/'capture';attempts=[];boxes=Counter();active=None;found=None
  with (src/'frontier.bin.attempts.bin').open('rb') as f:
   assert f.read(8)==b'RCATT001'
   while True:
    raw=f.read(256)
    if not raw:break
    a=struct.unpack('<32Q',raw);assert 1<=a[1]<=cut
    if a[0]==1:assert active is None;active=a;found=None;boxes[(a[1],a[2])+tuple(x-(1<<64) if x>=1<<63 else x for x in a[10:16])]+=1
    elif a[0]==2:assert active is not None and active[6]==a[6];found=a[28]
    elif a[0]==3:
     assert active is not None and active[6]==a[6];value=number(found) if found is not None else float('nan');status=2 if not math.isfinite(value) or value<0 else 1 if value==0 else 0;rn,rd=value.as_integer_ratio() if status==0 else (0,0);attempts.append((active[9],a[9],active[1],active[2],active[3],active[4],active[5],active[8],active[6],found,status,rn,rd));active=None
    else:raise AssertionError('unsupported metadata')
  assert active is None;expected={(x['phase'],x['net'],*x['box']):x['attempts'] for x in map(json.loads,Path(row['boxes']).open())};assert dict(boxes)==expected;ends=[a[1] for a in attempts];records={};nrecords=0
  for x in map(json.loads,Path(row['margins']).open()):
   key=x['net'],x['node'];pair=records.setdefault(key,{})
   assert x['horizon'] not in pair;nrecords+=1;x['_counts']=[0,0,0,0,0];x['_witness']=False;x['_ratio']=ratio(x['min_f_bits'],x['min_sink_f_bits']) if x['normalizable_events'] else None;pair[x['horizon']]=x
  checked=0
  with (src/'frontier.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   assert data[:8]==b'RCFRNT01'
   for off in range(8,len(data),144):
    if struct.unpack_from('<Q',data,off)[0]!=1:continue
    e=struct.unpack_from('<18Q',data,off);idx=bisect.bisect_left(ends,e[17]);a=attempts[idx];assert a[0]<e[17]<=a[1] and (e[1],e[2],e[3],e[4],e[8],e[10])==(a[2],a[3],a[4],a[5],a[6],a[7]);value=number(e[14]);status=3 if a[10]==2 else 2 if a[10]==1 else 4 if not math.isfinite(value) else 1
    if status==1:vn,vd=value.as_integer_ratio();n,d=vn*a[12],vd*a[11]
    candidates=records[e[2],e[7]];modes=['prefix','ready'] if e[1]==cut else ['prefix']
    for mode in modes:
     r=candidates[mode];r['_counts'][0]+=1;r['_counts'][status]+=1
     if status!=1:continue
     assert r['_ratio'] is not None;mn,md=r['_ratio'];left,right=n*md,mn*d;assert left>=right,(c,e[17],'not exact minimum')
     if left==right:assert e[17]>=r['min_event'],(c,'earlier equal ratio witness')
     if e[17]==r['min_event']:
      assert left==right and e[14]==r['min_f_bits'] and a[9]==r['min_sink_f_bits'] and a[8]==r['min_attempt'];r['_witness']=True
    checked+=1
  for pair in records.values():
   for r in pair.values():
    assert r['_counts']==[r[k] for k in ['accepted_events','normalizable_events','zero_target_events','invalid_target_events','nonfinite_candidate_events']]
    assert r['_witness']==bool(r['normalizable_events'])
  assert nrecords==row['margin_records'] and checked==row['prefix_accepted_events'];total_records+=nrecords;total_events+=checked;rows.append(dict(case=c,margin_records=nrecords,accepted_events=checked));print('EXACT_RATIONAL_MARGIN_INPUT_PASS',c,nrecords,checked,flush=True)
 assert len(rows)==6
 with (D/'independent_input_verification_v1.json').open('x') as f:json.dump(dict(status='ALL_RAW_ACCEPTED_EVENTS_CERTIFY_EXACT_MARGIN_MINIMA_AND_BOX_COUNTS',rows=rows,margin_records=total_records,accepted_events=total_events,bindings=bindings,method='Python float32-to-exact-integer-ratio cross products,not C++ dyadic ordering. Every raw event >= chosen minimum,earliest tie enforced,exact same-attempt witness found,all status counts and native box deduplication reconciled.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
