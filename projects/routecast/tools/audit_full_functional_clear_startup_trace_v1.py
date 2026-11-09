import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_functional_clear_startup_trace_v1_2026-10-09';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09'
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(S/n).read_bytes(),n
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(S/'tb.v').read_text()
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(r['exit_code']==0 for r in stages)
log=(D/'control.log').read_text();done=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert done
rows=[]
for line in log.splitlines():
 if 'FUNCTIONAL_CLEAR cycle=' not in line:continue
 line=line.replace('\\n',' ');row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line));row['cycle']=re.search(r'cycle=\s*(\d+)',line).group(1);rows.append(row)
assert len(rows)==512 and [int(r['cycle']) for r in rows]==list(range(512))
keys=['io','refill','exception','aw','ar','pipe_q','irq_q','cause','debug_q'];summary={}
for k in keys:
 known=[int(r['cycle']) for r in rows if not re.search('[xXzZ]',r[k])]
 summary[k]={'first_binary_postedge_cycle':min(known) if known else None,'binary_postedge_cycles':len(known),'first_four_values':[r[k] for r in rows[:4]]}
lanes={5:('io',0),2033:('pipe_q',0),3056:('irq_q',2),3059:('irq_q',3),3487:('refill',0),3490:('exception',0),3492:('aw',0),3494:('ar',0),3561:('cause',0),3562:('cause',1),3605:('debug_q',0),3606:('debug_q',1)}
lane_summary={}
for bit,(key,lane) in lanes.items():
 values=[r[key][-1-lane] for r in rows];known=[i for i,v in enumerate(values) if v in '01'];lane_summary[str(bit)]={'signal':key,'lane':lane,'first_binary_postedge_cycle':min(known) if known else None,'binary_postedge_cycles':len(known),'first_four_values':values[:4]}
out={'actual_12_lane_observations':lane_summary,'cycles':512,'mismatches':int(done.group(1)),'postedge_state_observations':summary,'rows':rows,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json','control.log']},'scope':'Original frozen full replay plus read-only post-edge observations. Post-edge controls are not pre-edge executed enables; binary source values do not prove source/native state equality, global initialization, or positive routing benefit.'}
(D/'startup_state_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
