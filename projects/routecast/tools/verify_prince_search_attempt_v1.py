"""All9 search attempt/context validation and exact prior observation identity."""
import json,subprocess,struct,tempfile,os,xml.etree.ElementTree as ET
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_search_attempt_trial_v1_2026-10-20';OLD=E/'prince_competitive_frontier_trial_v1_2026-10-20';B=R/'build/prince_search_attempt_audit_v1_2026-10-20/audit';BD=R/'build/prince_search_attempt_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def table(p,n):return [line.split()[:n] for line in p.open()]
def main():
 v=load(D/'verification.json');oldproof={r['case']:r for r in load(OLD/'branch_inference_verification_v1.json')['rows']};bindings={str(p):sha(p) for p in [D/'verification.json',D/'protocol.json',Path(__file__),B,R/'tools/audit_prince_search_attempt_v1.cpp',R/'tools/verify_prince_BB_conditional_demand_v1.py',BD/'source_invariance_v1.json']};assert len(v['rows'])==9
 prior=R/'build/prince_competitive_frontier_v1_2026-10-20';s=(BD/'connection_router.cpp').read_text();assert '\n'.join(line for line in s.splitlines() if '// RCATT' not in line).split()==(prior/'connection_router.cpp').read_text().split();assert (BD/'observer.cpp').read_text().startswith((prior/'observer.cpp').read_text())
 for p,h in load(BD/'receipt.json')['bindings'].items():assert sha(p)==h
 for width in [96,128,160]:
  graph=E/'prince_native_cohort_v1_2026-10-20'/f'w{width:03d}'/'source/rr_graph.xml';points={}
  for event,node in ET.iterparse(graph,events=['end']):
   if node.tag!='node':continue
   a=node.attrib
   if a.get('type') in ['CHANX','CHANY'] and int(a['capacity'])>0:
    loc=node.find('loc').attrib;high=a.get('direction')=='DEC_DIR';points[int(a['id'])]=tuple(int(loc[k]) for k in (['xhigh','yhigh'] if high else ['xlow','ylow']))+(int(loc.get('layer',0)),)
   node.clear()
  pp=B.parent/f'points_w{width:03d}.tsv';actual={int(f[0]):tuple(map(int,f[1:])) for f in (line.split() for line in pp.open())};assert points==actual
  for p in [graph,pp]:bindings[str(p)]=sha(p)
 def one(row):
  case=row['case'];d=D/case;old=OLD/case;assert row['callback_sequence_complete'] and row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal'];assert sha(old/'receipt.json')==oldproof[case]['receipt_sha256'];events=[int(line.split()[0]) for line in (d/'callback.tsv.ready.tsv').open() if int(line.split()[4])];cut=events[0] if events else row['iterations'];assert cut==oldproof[case]['cutoff'];memo={}
  def hashed(p):
   p=str(p)
   if p not in memo:memo[p]=sha(p)
   return memo[p]
  for name,n in [('callback.tsv',11),('callback.tsv.owners.tsv',10),('callback.tsv.ready.tsv',8)]:assert table(d/name,n)==table(old/name,n)
  names=['frontier.bin','frontier.bin.connection_ends.bin','frontier.bin.phases.tsv','queries.tsv','queries.tsv.connections.tsv','queries.tsv.ledger.bin',*[str(p.relative_to(d)) for p in (d/'boundary').glob('*.bin')],*[str(p.relative_to(d)) for p in (d/'owners').glob('*.bin')]]
  for name in names:assert hashed(d/name)==hashed(old/name),(case,name)
  point=B.parent/f"points_{case.split('/')[0]}.tsv";cp=subprocess.run([str(B),str(d),str(cut),str(point)],capture_output=True,text=True);assert cp.returncode==0,(case,cp.stderr);result=json.loads(cp.stdout);assert result['events_joined']==oldproof[case]['events'] and result['connections_without_attempt']==0 and result['unsupported']==0
  for p,h in row['files'].items():assert hashed(p)==h,(case,p)
  result.update(case=case,cutoff=cut,ready=bool(events),legacy_exact_parity_files=len(names),metadata_bytes=(d/'frontier.bin.attempts.bin').stat().st_size,receipt=str(d/'receipt.json'),receipt_sha256=sha(d/'receipt.json'))
  with (d/'attempt_verification_v1.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
  print('ATTEMPT_ALL_CHECKS_PASS',case,result['attempts'],result['failed'],result['retried_connections'],flush=True);return result
 with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(one,v['rows']))
 # Minimal real-record negative fixtures; source event streams only symlinked/read.
 original=D/'w096/episode_01/capture';f=(original/'frontier.bin.attempts.bin').open('rb');header=f.read(8);first=[list(struct.unpack('<32Q',f.read(256))) for _ in range(3)];f.close();assert [x[0] for x in first]==[1,2,3];guards=[]
 cases=[('epoch','attempt epoch'),('parameter','attempt parameter domain'),('watermark','attempt watermark gap'),('outcome','attempt outcome changed'),('geometry','preheap outside attempt BB')]
 for mode,expected in cases:
  with tempfile.TemporaryDirectory(prefix='rc_attempt_guard_') as td:
   temp=Path(td)
   for name in ['frontier.bin','frontier.bin.connection_ends.bin','queries.tsv.connections.tsv']:os.symlink(original/name,temp/name)
   a=[x.copy() for x in first]
   if mode=='epoch':a[0][8]+=1
   elif mode=='parameter':a[0][22]=0x7fc00000
   elif mode=='watermark':a[0][9]+=1
   elif mode=='outcome':a[2][28]^=1
   else:
    for x in a:x[10]=1000;x[11]=1000
   (temp/'frontier.bin.attempts.bin').write_bytes(header+b''.join(struct.pack('<32Q',*x) for x in a));cp=subprocess.run([str(B),str(temp),'27',str(B.parent/'points_w096.tsv')],capture_output=True,text=True);assert cp.returncode!=0 and expected in cp.stderr,(mode,cp.stderr);guards.append(dict(guard=mode,rejected_reason=expected))
 out=dict(status='ALL9_NATIVE_ATTEMPT_AND_EXACT_LEGACY_FRONTIER_PARITY_PASS',rows=rows,attempts=sum(r['attempts'] for r in rows),events_joined=sum(r['events_joined'] for r in rows),negative_guards=guards,bindings=bindings,scope='Independent attempt lifecycle/context/raw-word/domain/BB checks and exact prior fully validated CHANNEL bytes. Popped/stored sink cost equality measured,not assumed. Not an independent reconstruction of electrical path costs or proof of every uninstrumented native mode. No predictive/native-benefit/fullpaid/unseen/hardware admission.')
 with (D/'attempt_inference_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('ALL9_ATTEMPT_VERIFICATION_PASS',out['attempts'],out['events_joined'])
if __name__=='__main__':main()
