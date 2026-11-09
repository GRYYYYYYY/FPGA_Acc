"""Reuse actual postedge FF probes as next-preedge state without extra simulation."""
import re,json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09';log=(D/'control.log').read_text();tb=(D/'tb.v').read_text();a=json.loads((D/'trace_audit.json').read_text());assert a['replay_fidelity'];assert '#4;clk=0;if(i==2) begin reset=0;debugReset=0;end' in tb
bound={}
for c,i,v in re.findall(r'PIPE_BOUNDARY cycle=\s*(\d+) index=(\d+) value=([01x])',log):bound.setdefault(int(c),{})[int(i)]=v
logic=json.loads((R/'experiments/full_csr_capture_operand_aliases_v1_2026-10-09/audit.json').read_text());defs={r['node']:r for r in logic['records']}
def evaluate(node,vals):
 d=defs[node];poss=[['0','1'] if vals[i['input']]=='x' else [vals[i['input']]] for i in d['inputs']];rows=[r.split() for r in d['actual_cubes']];pol=rows[0][1];out=set()
 for bits in itertools.product(*poss):
  hit=any(all(p=='-' or p==b for p,b in zip(pattern,bits)) for pattern,_ in rows);out.add(pol if hit else str(1-int(pol)))
 return next(iter(out)) if len(out)==1 else 'x'
rows=[];guard=[]
for cycle in range(4,142):
 b=bound[cycle-1];vals={'b2018':b[2],'b602':b[23],'b574':b[20],'b2016':b[1],'b3451':b[6],'b3447':b[4],'b3449':b[5]};vals['new_n5939']=evaluate('new_n5939',vals);value=evaluate('new_n5938',vals);observed=a['rows'][cycle]['new_n5938'];assert value==observed,(cycle,vals,value,observed)
 rows.append({'cycle':cycle,'previous_postedge_cycle':cycle-1,'values':vals,'observed_n5938':observed})
 if vals['b3451']=='0':assert value==vals['b2016'];guard.append(cycle)
assert 5 in guard and rows[1]['values']['b2016']=='x'
out={'matched_preedge_rows':len(rows),'execute_invalid_mask_cycles':guard,'first_capture_unknown_witness':rows[1],'conclusion':'Actual previous-postedge FF state reconstructs preedge n5938 for cycles4..141. When native executeValid0, n5938 equals flusher counter highbit, independent of unknown CSR/memory-management flags. Cycle5 unknown counter high (observed postedge4) directly explains earliest captureX.','scope':'Uses no intervening positive edge and no reset assertion after cycle2 from actual tb. Local observed four-state history, not proof of all42370 cause or counter high D root cause.','rows':rows,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['tb.v','control.log','trace_audit.json']}}
O=R/'experiments/full_csr_capture_counter_history_v1_2026-10-09';O.mkdir(exist_ok=True);(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'matched':len(rows),'invalid_guard_cycles':len(guard),'witness':rows[1]},indent=2))
