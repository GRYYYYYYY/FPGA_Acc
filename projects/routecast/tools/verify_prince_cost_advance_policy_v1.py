"""Independent mode/epoch/pres-scalar and all-CHANNEL global-history replay."""
import json,struct,mmap
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_cost_advance_ablation_trial_v1_2026-10-20';MODES=dict(native=0,hold_pres=1,hold_acc=2,hold_both=3)
def load(p):return json.loads(Path(p).read_text())
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def number(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def epochs(path):
 result={};epoch=0
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
  off=0
  def word():
   nonlocal off
   x=struct.unpack_from('<Q',raw,off)[0];off+=8;return x
  while off<len(raw):
   tag,e=word(),word()
   if tag in [1,4]:assert e==epoch+1;epoch=e;word();word();n=word();off+=n*8
   elif tag==2:assert e==epoch;word();word();word();word();n=word();off+=n*8
   elif tag==3:assert e==epoch;i=word();assert i==len(result)+1;result[i]=e
   elif tag==5:
    assert e==epoch;n=word()
    for _ in range(n):word();count=word();off+=count*8
    assert off==len(raw)
   else:raise AssertionError(tag)
 return result

def one(row):
 full=row['case'];base,mode=full.rsplit('/',1);m=MODES[mode];d=D/full;control=D/base/'native';ready=row['ready_iteration'];native=load(control/'receipt.json');assert ready==native['ready_iteration'];identity=(d/'identity.txt').read_text().splitlines();policy=(d/'cost_policy.txt').read_text().splitlines();assert policy==['COST_ADVANCE_ABLATION_V1',mode,base,identity[3],identity[6]];meta=load(d/'policy_mode.json');assert meta['mode']==mode and meta['policy_sha256']==sha(d/'cost_policy.txt');pl=(d/'queries.tsv.cost_policy_load.tsv').read_text().strip().split();assert pl==[str(m),mode,base,identity[3],identity[6],(d/'callback.tsv.resolved.sha256').read_text().strip()];cfg={a[0]:int(a[2]) for a in (line.split() for line in (d/'callback.tsv.resolved.tsv').open()) if a[1]=='f32'};assert sha(d/'callback.tsv.resolved.tsv')==sha(control/'callback.tsv.resolved.tsv');cb={int(x[0]):list(map(int,x)) for x in (line.split() for line in (d/'callback.tsv').open())};q={int(x[0]):list(map(int,x)) for x in (line.split() for line in (d/'queries.tsv').open())};cq={int(x[0]):list(map(int,x)) for x in (line.split() for line in (control/'queries.tsv').open())};ep=epochs(d/'queries.tsv.ledger.bin');acc={};pres={}
 for line in (d/'queries.tsv.cost_advances.tsv').open():
  tag,i,r,actual_mode,a,b,effective,armed,epoch,observed_phase=map(int,line.split());assert actual_mode==m and epoch==ep[i]
  expected_ready=ready if ready is not None and (i>ready if tag==1 else i>=ready) else 0;assert r==expected_ready and armed==int(bool(r))
  if tag==1:
   assert observed_phase==i-1 and b==0 and a==(0 if i==1 else cfg['t_router_opts.acc_fac']);expected=0 if r and m&2 else a;assert effective==expected and i not in acc;acc[i]=effective
  else:
   assert tag==2 and observed_phase==i and i>=2 and a==cb[i][3] and b==cfg['t_router_opts.pres_fac_mult'];expected=a if r and m&1 else bits(number(a)*number(b));assert effective==expected and i not in pres;pres[i]=effective
 assert set(acc)==set(cb)==set(q)==set(ep);previous={};channel_checks=0;allrr_checks=0;changed_acc=0;prefix_count=0
 for i in sorted(cb):
  expected_pres=cfg['t_router_opts.first_iter_pres_fac'] if i==1 else cfg['t_router_opts.initial_pres_fac'] if i==2 else bits(min(number(pres[i-1]),number(cfg['t_router_opts.max_pres_fac'])));assert cb[i][3]==expected_pres
  p=d/'boundary'/f'iteration_{i}.bin';raw=p.read_bytes();assert raw[:8]==b'RCBND001' and struct.unpack_from('<Q',raw,8)[0]==i;current={};overused=total=worst=0;factor=number(acc[i])
  for n,kind,occ,cap,w in struct.iter_unpack('<QIiiI',raw[24:]):
   over=max(0,occ-cap);overused+=over>0;total+=over;worst=max(worst,over);allrr_checks+=1
   if kind not in [4,5]:continue
   old=previous.get(n,1065353216);expected=bits(number(old)+number(bits(over*factor))) if over and factor else old;assert w==expected,(full,i,n,w,expected);changed_acc+=w!=old;current[n]=w;channel_checks+=1
  assert [overused,total,worst]==cb[i][4:7];previous=current
  if ready is None or i<=ready:
   assert q[i]==cq[i]
   for name in [f'boundary/iteration_{i}.bin',f'boundary/boxes_{i}.bin',f'owners/owners_{i}.bin']:assert sha(d/name)==sha(control/name),(full,i,name)
   prefix_count+=1
 first_post=False
 if mode=='hold_acc' and ready is not None:
  i=ready+1;assert q[i]==cq[i]
  for name in [f'boundary/boxes_{i}.bin',f'owners/owners_{i}.bin']:assert sha(d/name)==sha(control/name)
  first_post=True
 for p,h in row['files'].items():assert sha(p)==h
 out=dict(case=full,status='MODE_EFFECTIVE_FACTOR_EPOCH_AND_CHANNEL_HISTORY_REPLAY_PASS',CHANNEL_history_checks=channel_checks,all_RR_overuse_checks=allrr_checks,changed_CHANNEL_acc_words=changed_acc,prefix_parity_phases=prefix_count,hold_acc_first_post_search_identity=first_post)
 with (d/'policy_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 return out

def main():
 vp=D/'verification.json';v=load(vp);assert len(v['rows'])==36;rows=[]
 with ProcessPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(one,r) for r in v['rows']]):
   row=future.result();rows.append(row);print('COST_POLICY_REPLAY_PASS',row['case'],row['CHANNEL_history_checks'],flush=True)
 assert sum(r['hold_acc_first_post_search_identity'] for r in rows)==6
 with (D/'policy_inference_verification_v1.json').open('x') as f:json.dump(dict(status='ALL36_POLICY_EPOCH_PRES_GLOBAL_CHANNEL_ACC_AND_PREFIX_GUARDS_PASS',rows=sorted(rows,key=lambda r:r['case']),CHANNEL_history_checks=sum(r['CHANNEL_history_checks'] for r in rows),all_RR_overuse_checks=sum(r['all_RR_overuse_checks'] for r in rows),bindings={str(p):sha(p) for p in [vp,Path(__file__)]},scope='CHANNEL global-history recurrence and all-RR overuse counts independently replayed. Local OPIN history remains native;no claim all possible history operations frozen. No predictive/fullpaid/unseen admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
