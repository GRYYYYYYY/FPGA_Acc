"""Early ready-control masks from actual BLIF and retained FF observations."""
import json,re,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_ready_early_masks_v1_2026-10-09';D.mkdir(exist_ok=True)
B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';ls=B.read_text().splitlines();nodes={}
for i,line in enumerate(ls):
 if not line.startswith('.names '):continue
 rows=[]
 for t in ls[i+1:]:
  if t.startswith('.'):break
  if t.strip():rows.append(t.split())
 nodes[line.split()[-1]]={'inputs':line.split()[1:-1],'rows':rows}
def ev(n,v):
 d=nodes[n];pol=d['rows'][0][1];out=set()
 for bits in itertools.product(*[['0','1'] if v[b]=='x' else [v[b]] for b in d['inputs']]):
  hit=any(all(p=='-' or p==b for p,b in zip(pattern,bits)) for pattern,_ in d['rows']);out.add(pol if hit else str(1-int(pol)))
 return next(iter(out)) if len(out)==1 else 'x'
assert ev('new_n6084',{'b3409':'0','b3407':'0','b3387':'0'})=='1'
for a,b in itertools.product('01x',repeat=2):
 assert ev('new_n6072',{'new_n6073':a,'b2138':b,'b3441':'0','new_n6084':'1'})=='1'
 assert ev('new_n6086',{'new_n6098':a,'new_n6087':b,'new_n6072':'1'})=='0'
for a,b,c in itertools.product('01x',repeat=3):
 assert ev('new_n6107',{'new_n6072':'1','b1848':a,'b3533':b,'b3817':c})=='0'
 assert ev('new_n6110',{'b568':a,'b3447':'0'})=='0'
 assert ev('new_n6109',{'b572':a,'b3451':'0','b3449':'0','b570':b,'new_n6110':'0'})=='1'
P=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';log=(P/'control.log').read_text();tb=(P/'tb.v').read_text();assert '#4;clk=0;if(i==2) begin reset=0;debugReset=0;end' in tb
bound={}
for cy,ix,val in re.findall(r'PIPE_BOUNDARY cycle=\s*(\d+) index=(\d+) value=([01x])',log):bound.setdefault(int(cy),{})[int(ix)]=val
cycles=[cy for cy in range(4,142) if all(bound[cy-1][i]=='0' for i in [4,5,6])];assert 5 in cycles
out={'nodes':{n:nodes[n] for n in ['new_n6084','new_n6072','new_n6086','new_n6107','new_n6110','new_n6109','new_n6111']},'all_pipeline_invalid_cycles':cycles,'conclusion':'With known debugFSM000 and IBusdecodeValid0,6072=1/6086=0/6107=0 independent of cache/debug flags. With WB/MEM/EXvalid0,6109=1 independent of unknown ENV flags. These leave capture6108 and MMU6111 as early6085 inputs.','scope':'Actual BLIF truth evaluation and observed pipeline-valid FF history. DebugFSM idle/export composition was separately verified, not newly traced; IBusvalid preedge is actualready pin0. MMU6111 known history and complete export binding of these masks remain open.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [B,P/'control.log',P/'tb.v']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'pipeline_invalid_cycles':len(cycles),'first_cycles':cycles[:5],'conclusion':out['conclusion']},indent=2))
