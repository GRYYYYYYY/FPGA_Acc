"""Actual fixed replay fidelity and pre-edge source tag initialization coverage."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09';B=E/'full_source_export_fixed_bus_replay_v19_2026-10-09';protocol=json.load(open(P/'protocol.json'));sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
for f,h in protocol['bindings'].items():assert sha(Path(f))==h
assert sha(B/'fixed_replay_audit.json')==protocol['baseline_audit_sha256']
for n in ['reference.v','design.v','primitives.v','control.py','run.py','frozen_bus_trace.json']:assert (P/n).read_bytes()==(B/n).read_bytes()
extra=(P/'added_displays.txt').read_text();assert (P/'tb.v').read_text()==(B/'tb.v').read_text().replace(' clk=1;#1;compare;',extra+' clk=1;#1;compare;')
stages=json.load(open(P/'stages.json'));assert len(stages)==3 and all(r['exit_code']==0 for r in stages);log=(P/'control.log').read_text();assert 'Fatal' not in log;parent=(B/'control.log').read_text();counts={}
for prefix in ['BUS_INPUT','COUNTER_CONTROL','PIPE_BOUNDARY','DATA_FLUSH','PIPE_NODE','FLUSH_CONTROL','READ_CONTROL','TAG_READ','TAG_STATE','FILL_STATE','CACHE_STATE','DIFF','IBUS_COVERAGE','ROUTECAST_FULL_COMPARE_DONE']:
 rx=r'@"('+prefix+r'[^\n]*?)\\n"';actual=re.findall(rx,log);assert actual==re.findall(rx,parent),prefix;counts[prefix]=len(actual)
rx=r'@"STARTUP_TAG_WRITE cycle=\s*(\d+) reset=([01xz]) mem=(ibus|dbus) we=([01xz]) addr=([0-9a-fxz]+) valid=([01xz]) flush=([0-9a-fxz]+) re=([01xz]) readaddr=([0-9a-fxz]+)\\n"';raw=re.findall(rx,log);assert len(raw)==1024;results={}
for mem in ['ibus','dbus']:
 rows=[{'cycle':int(t[0]),'reset':t[1],'we':t[3],'addr':t[4],'valid':t[5],'flush':t[6],'re':t[7],'readaddr':t[8]} for t in raw if t[2]==mem];assert [r['cycle'] for r in rows]==list(range(512));cleared=set();ever_written=set();clear_events=[];reads_before_write=[];uncertain=[];full_cycle=None;first_read=None
 for r in rows:
  if r['re']=='1':
   if first_read is None:first_read=r['cycle']
   if any(x in r['readaddr'] for x in 'xz') or int(r['readaddr'],16) not in ever_written:reads_before_write.append(r)
  if r['we']=='1':
   if any(x in r['addr'] for x in 'xz') or r['valid'] not in '01':uncertain.append(r);continue
   addr=int(r['addr'],16);assert 0<=addr<128;ever_written.add(addr)
   if r['valid']=='0':cleared.add(addr);clear_events.append({'cycle':r['cycle'],'addr':addr,'reset':r['reset']})
   if len(cleared)==128 and full_cycle is None:full_cycle=r['cycle']
  elif r['we'] in 'xz':uncertain.append(r)
 results[mem]={'records':rows,'invalidating_write_events':clear_events,'unique_ever_invalidated_lines':len(cleared),'first_all_128_ever_invalidated_cycle':full_cycle,'first_read_enable_cycle':first_read,'reads_without_prior_known_write':reads_before_write,'uncertain_write_events':uncertain,'scope':'Source pre-edge signals for this frozen 512-cycle trace; ever-invalidated coverage is not simultaneous invalidity or native-wrapper physical commit/Full initialization proof.'}
out={'fixed_replay_fidelity':True,'matched_counts':counts,'results':results,'functional_admission':False,'scope':'Original failing comparison preserved. Startup source coverage only; no arbitrary-reset universal claim, native memory equivalence, invalid-tag error/address masking or physical initialization claim.','bindings':{str(f):sha(f) for f in [Path(__file__),P/'protocol.json',P/'control.log',P/'stages.json',B/'control.log']}};(P/'startup_tag_write_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({m:{k:v for k,v in r.items() if k not in ['records','invalidating_write_events']} for m,r in results.items()},indent=2))
