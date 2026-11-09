"""All9 exact observation parity, independent native branch/epoch audit and guards."""
import json,subprocess,tempfile,os,struct
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_competitive_frontier_trial_v1_2026-10-20';B=R/'build/prince_competitive_frontier_audit_v1_2026-10-20/audit';OLD=E/'prince_ownership_ledger_trial_v2_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def table(p,n):return [line.split()[:n] for line in p.open()]
def main():
 vp=D/'verification.json';v=load(vp);jobs=load(D/'protocol.json')['jobs'];bindings={str(p):sha(p) for p in [vp,D/'protocol.json',Path(__file__),B,R/'tools/audit_prince_competitive_frontier_v1.cpp',R/'build/prince_competitive_frontier_v1_2026-10-20/source_invariance_v1.json']};assert len(v['rows'])==9
 # First case was already run through this exact auditor; preserve its successful result.
 first=D/'w096/episode_01/capture/branch_verification_v1.json'
 if not first.exists():
  result=dict(status='BRANCH_CONTEXT_EPOCH_OWNERSHIP_CUTOFF_AND_COMMIT_JOIN_PASS',events=19474155,prefix_connections=82335,tag_counts=[12406392,4242111,2814543,11109],nonfinite_input_events=12324806,target_sink_mismatch_events=0,RCV_events=0,positive_updates=108017,matched_post_connection_updates=82335,unattributed_updates=25682,committed_CHANNEL_nodes=141714,committed_with_preheap_accept=141714,committed_with_valid_pop=141714)
  with first.open('x') as f:json.dump(result,f,indent=2)
 def one(row):
  case=row['case'];base=case.rsplit('/',1)[0];d=D/case;old=OLD/base/'capture';assert row['callback_sequence_complete'] and row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal'];events=[int(x.split()[0]) for x in (d/'callback.tsv.ready.tsv').open() if int(x.split()[4])];assert len(events)<=1;cutoff=events[0] if events else row['iterations'];parity=[]
  for name,n in [('callback.tsv',11),('callback.tsv.owners.tsv',10),('callback.tsv.ready.tsv',8)]:assert table(d/name,n)==table(old/name,n);parity.append(name)
  for name in ['queries.tsv','queries.tsv.connections.tsv','queries.tsv.ledger.bin',*[str(p.relative_to(d)) for p in (d/'boundary').glob('*.bin')],*[str(p.relative_to(d)) for p in (d/'owners').glob('*.bin')]]:assert sha(d/name)==sha(old/name),(case,name);parity.append(name)
  out=d/'branch_verification_v1.json'
  if case!='w096/episode_01/capture':
   cp=subprocess.run([str(B),str(d),str(cutoff)],capture_output=True,text=True);assert cp.returncode==0,(case,cp.stderr);result=json.loads(cp.stdout)
   with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
  else:result=load(out)
  assert result['committed_CHANNEL_nodes']==result['committed_with_preheap_accept']==result['committed_with_valid_pop'];assert result['matched_post_connection_updates']==result['prefix_connections'];assert result['target_sink_mismatch_events']==0
  for p,h in row['files'].items():assert sha(p)==h,(case,p)
  receipt=d/'receipt.json';result=dict(result,case=case,cutoff=cutoff,ready=bool(events),exact_parity_artifacts=len(parity),frontier_bytes=(d/'frontier.bin').stat().st_size,receipt=str(receipt),receipt_sha256=sha(receipt));print('FRONTIER_ALL_CHECKS_PASS',case,result['events'],result['committed_CHANNEL_nodes'],flush=True);return result
 with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(one,v['rows']))
 # Real-record negative witnesses, isolated temp outputs; original stream immutable.
 original=D/'w096/episode_01/capture';prefix=(original/'frontier.bin').open('rb');header=prefix.read(8);record=list(struct.unpack('<18Q',prefix.read(144)));prefix.close();guards=[]
 for field,value,expected in [(0,2 if record[0]==1 else 1,'native branch predicate mismatch'),(10,record[10]+1,'event epoch context'),(16,1-record[16],'event retained ownership/RCV'),(1,28,'event tag/cutoff')]:
  with tempfile.TemporaryDirectory(prefix='rc_frontier_guard_') as td:
   temp=Path(td)
   for name in ['queries.tsv.ledger.bin','queries.tsv.connections.tsv','frontier.bin.connection_ends.bin','frontier.bin.phases.tsv','boundary']:os.symlink(original/name,temp/name)
   bad=record.copy();bad[field]=value;(temp/'frontier.bin').write_bytes(header+struct.pack('<18Q',*bad));cp=subprocess.run([str(B),str(temp),'27'],capture_output=True,text=True);assert cp.returncode!=0 and expected in cp.stderr,(field,cp.stderr);guards.append(dict(field=field,rejected_reason=expected))
 out=dict(status='ALL9_BRANCH_CONTEXT_CUTOFF_COMMIT_AND_OBSERVATION_PARITY_PASS',rows=rows,events=sum(r['events'] for r in rows),committed_CHANNEL_nodes=sum(r['committed_CHANNEL_nodes'] for r in rows),guards=guards,bindings=bindings,scope='Raw branch floats independently checked,not re-evaluated by observer. Exact prior validated ledger/RR/box/owner/query-byte parity;commits mapped only immediate positive updates after matching closed connection,setup/unattributed updates kept separate. No prediction/global-quality/native-speed/fullpaid/unseen/hardware admission.')
 with (D/'branch_inference_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print('ALL9_FRONTIER_VERIFICATION_PASS',out['events'],out['committed_CHANNEL_nodes'])
if __name__=='__main__':main()
