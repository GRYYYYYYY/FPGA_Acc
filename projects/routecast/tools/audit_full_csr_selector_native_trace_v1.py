"""Audit terminal display-only full replay and paired selector capture observations."""
import json,re,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_native_tag_access_path_trace_v1_2026-10-09';D=R/'experiments/full_csr_selector_native_trace_v1_2026-10-09'
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages),'Replay not yet terminal-successful'
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(P/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(P/'tb.v').read_text()
log=(D/'control.log').read_text();parent=(P/'control.log').read_text()
def old_records(s):return [line.strip() for line in s.splitlines() if re.search(r'\b(?:BUS_INPUT|DIFF|ROUTECAST_FULL_COMPARE_DONE)\b',line)]
assert old_records(log)==old_records(parent),'Original comparison/input records changed'
done=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert done and int(done[1])==42370
rows=[]
for line in log.splitlines():
 if 'CSR_SELECTOR_PREEDGE cycle=' not in line:continue
 row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line.replace('\\n',' ')));row['cycle']=int(re.search(r'cycle=\s*(\d+)',line)[1]);rows.append(row)
assert len(rows)==512 and [r['cycle'] for r in rows]==list(range(512))
first=lambda key:next((r['cycle'] for r in rows if r[key]=='1'),None)
out={'cycles':512,'mismatches':42370,'replay_fidelity':True,'first_source_capture':first('src_en'),'first_native_capture':first('native_capture_node'),'capture_pairs':dict(collections.Counter(r['src_en']+'/'+r['native_capture_node'] for r in rows)),'known_instruction_equal_capture_cycles':[r['cycle'] for r in rows if r['src_en']==r['native_capture_node']=='1' and re.fullmatch('[01]+',r['src_instruction']) and r['src_instruction']==r['native_instruction']],'instruction_observation_differences':[r['cycle'] for r in rows if r['src_instruction']!=r['native_instruction']],'selector_observation_differences':[r['cycle'] for r in rows if r['src_select']!=r['native_select']],'rows':rows,'scope':'Actual512source/export preedge observations preserving full frozen comparison. X string agreement is not initialized equality proof; native node binary capture semantics separately audited. No global admission.','hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log','stages.json']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','instruction_observation_differences','selector_observation_differences','known_instruction_equal_capture_cycles']},indent=2));print('instruction differing cycles',len(out['instruction_observation_differences']),'selector differing cycles',len(out['selector_observation_differences']),'known equal captures',len(out['known_instruction_equal_capture_cycles']))
