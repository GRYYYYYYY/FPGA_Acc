"""Native thread CPU versus wall call clocks, validated scopes and full corpus counts."""
import json,re,sys
from pathlib import Path
from pre_route_endpoints import sha
D=Path(sys.argv[1]).resolve();P=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None;proof=json.loads((D/'verification.json').read_text());assert proof['all_cases_both_complete_arms_authenticated'] and all(sha(p)==h for p,h in proof['bindings'].items());files=[Path(__file__).resolve(),D/'verification.json'];rows=[]
def parse(log,label):
 text=log.read_text();cp=list(re.finditer(r'ROUTECAST_CPU phase=(\d+) bidi_wall=([0-9.]+) bidi_cpu=([0-9.]+) forward_wall=([0-9.]+) forward_cpu=([0-9.]+)',text));wp=list(re.finditer(r'ROUTECAST_PROFILE phase=(\d+) bidi=(\d+) forward=(\d+) kernel=([0-9.]+)',text));assert [int(m[1]) for m in cp]==[0,1,2] and [int(m[1]) for m in wp]==[0,1,2];out=[]
 for c,w in zip(cp,wp):
  bwall,bcpu,fwall,fcpu=map(float,c.group(2,3,4,5));assert bcpu>=0 and fcpu>=0 and bcpu<=bwall+.01 and fcpu<=fwall+.01;assert abs(bwall+fwall-float(w[4]))<1e-6;out.append(dict(phase=int(c[1]),bidi_calls=int(w[2]),forward_calls=int(w[3]),bidi_wall=bwall,bidi_cpu=bcpu,forward_wall=fwall,forward_cpu=fcpu))
 assert sum(r['bidi_calls']+r['forward_calls'] for r in out)==7459
 totals={k:sum(r[k] for r in out) for k in ['bidi_wall','bidi_cpu','forward_wall','forward_cpu']};totals['kernel_wall']=totals['bidi_wall']+totals['forward_wall'];totals['kernel_cpu']=totals['bidi_cpu']+totals['forward_cpu'];totals['kernel_wall_outside_thread_cpu']=totals['kernel_wall']-totals['kernel_cpu'];files.append(log);return dict(case=label,phases=out,totals=totals)
rows.append(parse(D/'seed/native/sha1/native.log','fresh_live_feedback'))
if P:
 p=P/'receipt.json';v=json.loads(p.read_text());assert v['all2_complete_corpus_replays_pass'] and all(sha(q)==h for q,h in v['bindings'].items());assert len(v['rows'])==2;files.append(p)
 for row in v['rows']:
  assert row['exit_code']==0 and row['matched_receive_lines']==24640 and row['all_response_lines_and_native_route_bytes_equal'];rows.append(parse(P/f"{row['index']}_{row['variant']}"/'native.log',f"matched_replay_{row['index']}"))
files.append(D/'wire_transaction_verification.json');(D/'cpu_wall_analysis.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},rows=rows,scope='Same calls thread CPU and wall clocks; CPU indicates scheduled native-thread work, wall minus CPU can include descheduling/pagefault/blocking, not an attribution to a particular cgroup/job. Separate live/replay controller/cache environments; no clock summing or general speedup/heldout claim. Timer overhead not subtracted.'),indent=2)+'\n');print(json.dumps([{k:r[k] for k in ['case','totals']} for r in rows],indent=2))
