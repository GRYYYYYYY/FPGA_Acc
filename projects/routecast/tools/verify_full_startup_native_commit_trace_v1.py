"""Source-to-native pending write observation, phase aligned without discarding unknowns."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_source_export_startup_native_commit_trace_v22_2026-10-09';B=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();protocol=json.load(open(P/'protocol.json'))
for f,h in protocol['bindings'].items():assert sha(Path(f))==h
assert sha(B/'startup_tag_write_audit.json')==protocol['baseline_audit_sha256']
for n in ['reference.v','design.v','primitives.v','control.py','run.py','frozen_bus_trace.json']:assert (P/n).read_bytes()==(B/n).read_bytes()
extra=(P/'added_displays.txt').read_text();assert (P/'tb.v').read_text()==(B/'tb.v').read_text().replace(' clk=1;#1;compare;',extra+' clk=1;#1;compare;');stages=json.load(open(P/'stages.json'));assert len(stages)==3 and all(s['exit_code']==0 for s in stages);log=(P/'control.log').read_text();parent=(B/'control.log').read_text();assert 'Fatal' not in log;counts={}
for prefix in ['BUS_INPUT','COUNTER_CONTROL','PIPE_BOUNDARY','DATA_FLUSH','PIPE_NODE','FLUSH_CONTROL','READ_CONTROL','TAG_READ','TAG_STATE','FILL_STATE','CACHE_STATE','DIFF','IBUS_COVERAGE','ROUTECAST_FULL_COMPARE_DONE','STARTUP_TAG_WRITE']:
 rx=r'@"('+prefix+r'[^\n]*?)\\n"';actual=re.findall(rx,log);assert actual==re.findall(rx,parent),prefix;counts[prefix]=len(actual)
raw=re.findall(r'@"STARTUP_NATIVE_COMMIT cycle=\s*(\d+) mem=(ibus|dbus) we=([01xz]) addr=([0-9a-fxz]+) valid=([01xz])\\n"',log);assert len(raw)==1024;source=json.load(open(B/'startup_tag_write_audit.json'));results={}
for mem in ['ibus','dbus']:
 rows=[{'cycle':int(t[0]),'we':t[2],'addr':t[3],'valid':t[4]} for t in raw if t[1]==mem];assert [r['cycle'] for r in rows]==list(range(512));initial=rows[0];assert initial['we']=='0';src=source['results'][mem]['records'];cleared=set();events=[];uncertain=[];we_diff=[];enabled_diff=[];first_full=None
 for r in rows:
  i=r['cycle']
  if i>0:
   expected=src[i-1]
   if r['we']!=expected['we']:we_diff.append({'native':r,'prior_source':expected})
   if r['we']=='1' and expected['we']=='1' and (r['addr']!=expected['addr'] or r['valid']!=expected['valid']):enabled_diff.append({'native':r,'prior_source':expected})
  if r['we']=='1':
   if any(x in r['addr'] for x in 'xz') or r['valid'] not in '01':uncertain.append(r);continue
   addr=int(r['addr'],16);assert 0<=addr<128
   if r['valid']=='0':cleared.add(addr);events.append(r)
   if len(cleared)==128 and first_full is None:first_full=i
  elif r['we'] in 'xz':uncertain.append(r)
 results[mem]={'rows':rows,'initial_pending':initial,'known_invalidating_events':events,'unique_ever_known_invalidated_lines':len(cleared),'first_all_128_ever_known_invalidated_cycle':first_full,'uncertain_commit_events':uncertain,'phase_aligned_write_enable_differences':we_diff,'phase_aligned_enabled_payload_differences':enabled_diff,'scope':'Native pending WE/address/valid sampled before edge. Known we=1/valid0 addresses are predicted commits under macro semantics, not direct array-content observation. Unknown WE/value/address preserved. Pending phase aligned to prior source row; source/native controls may diverge.'}
out={'replay_fidelity':True,'matched_record_counts':counts,'results':results,'functional_admission':False,'scope':'Actual frozen failing Full trace observations, not a functional repair or arbitrary reset theorem; pending register probes are not direct physical-board memory evidence.','bindings':{str(f):sha(f) for f in [Path(__file__),P/'protocol.json',P/'control.log',P/'stages.json',B/'startup_tag_write_audit.json']}};(P/'native_commit_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({m:{'known_invalidated':r['unique_ever_known_invalidated_lines'],'full_cycle':r['first_all_128_ever_known_invalidated_cycle'],'unknown_events':len(r['uncertain_commit_events']),'we_diff':len(r['phase_aligned_write_enable_differences']),'payload_diff':len(r['phase_aligned_enabled_payload_differences']),'first_we_diff':r['phase_aligned_write_enable_differences'][:1]} for m,r in results.items()},indent=2))
