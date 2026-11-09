"""Join actual first-reset-release observation with exact exported LUT cover."""
import hashlib,itertools,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';C=E/'full_flush_capture_preedge_v1_2026-10-09/capture_audit.json';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';V=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/design.v';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';a=json.loads(C.read_text());r=a['observations'][3];pre=r['pre'];post=r['post'];assert pre['reset']=='0' and pre['src_start']==pre['native_start']=='1';assert pre['src_single']==pre['native_gate']=='x';assert pre['src_line']=='xxxxxxx' and pre['src_q']==post['src_q']=='00000000';assert pre['native_q6']=='0' and pre['native_d6']==post['native_q6']=='x'
export_order=['b2016','new_n6607','b518','b2014','new_n6618','b3121'];text=V.read_text()
for i,n in enumerate(export_order):assert re.search(r'routing_segment_[^\n]*'+re.escape(n)+r'_output_0_0_to_lut_b2013_input_0_'+str(i),text)
actual=list(reversed(pre['native_d6_inputs']));assert len(actual)==6;values=dict(zip(export_order,actual));assert values=={'b2016':'0','new_n6607':'x','b518':'x','b2014':'0','new_n6618':'0','b3121':'1'}
lines=B.read_text().splitlines();i=next(i for i,l in enumerate(lines) if l.startswith('.names ') and l.endswith(' b2013'));names=lines[i].split()[1:-1];rows=[]
for line in lines[i+1:]:
 if line.startswith('.'):break
 if line.strip():rows.append(line.split())
assert {row[-1] for row in rows}=={'1'};results=[]
for gate,line in itertools.product('01',repeat=2):
 v=values|{'new_n6607':gate,'b518':line};inputs=[v[n] for n in names];y=str(int(any(all(p=='-' or p==x for p,x in zip(row[0],inputs)) for row in rows)));assert y==str(int(gate=='0' and line=='1'));results.append({'zero_detector':gate,'line_address_lane6':line,'native_D6':y})
assert {x['native_D6'] for x in results}=={'0','1'}
source=S.read_text();assert "stageB_flusher_counter <= 8'h0;" in source and 'if(io_cpu_flush_payload_singleLine) begin' in source
out={'cycle':3,'actual_export_input_values':values,'binary_completions':results,'actual_native_pre_D6':pre['native_d6'],'actual_native_post_Q6':post['native_q6'],'actual_source_post_counter':post['src_q'],'interpretation':'At actual released edge start1 overrides prior increment. Original procedural singleLine if(X) skips line-address assignment, leaving counter0; actual synthesized LUT admits binary completions with different D6 and capturesX. Both representations agree for each known binary gate/address combination in this local start1 update, but four-state operational behavior differs.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [C,B,V,S]},'scope':'Actual cycle3 local lane6 origin under frozen startup; not explanation of all42370 mismatches, actual hardware failure, global source/native relation, or scientific performance admission.'}
d=E/'full_flush_first_capture_origin_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'origin_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='hashes'},indent=2))
