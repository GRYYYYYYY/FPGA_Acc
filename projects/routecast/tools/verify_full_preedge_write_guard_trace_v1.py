"""Actual pre-edge priority values, replay fidelity and pending phase."""
from pathlib import Path
import json,re,hashlib,itertools
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_source_export_preedge_write_guard_trace_v23_2026-10-09';B=E/'full_source_export_startup_native_commit_trace_v22_2026-10-09';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();protocol=json.load(open(P/'protocol.json'))
for f,h in protocol['bindings'].items():assert sha(Path(f))==h
assert sha(B/'native_commit_audit.json')==protocol['baseline_audit_sha256']
for n in ['reference.v','design.v','primitives.v','control.py','run.py','frozen_bus_trace.json']:assert (P/n).read_bytes()==(B/n).read_bytes()
extra=(P/'added_displays.txt').read_text();assert (P/'tb.v').read_text()==(B/'tb.v').read_text().replace(' clk=1;#1;compare;',extra+' clk=1;#1;compare;');stages=json.load(open(P/'stages.json'));assert len(stages)==3 and all(r['exit_code']==0 for r in stages);log=(P/'control.log').read_text();parent=(B/'control.log').read_text();assert 'Fatal' not in log;counts={}
for prefix in ['BUS_INPUT','COUNTER_CONTROL','PIPE_BOUNDARY','DATA_FLUSH','PIPE_NODE','FLUSH_CONTROL','READ_CONTROL','TAG_READ','TAG_STATE','FILL_STATE','CACHE_STATE','DIFF','IBUS_COVERAGE','ROUTECAST_FULL_COMPARE_DONE','STARTUP_TAG_WRITE','STARTUP_NATIVE_COMMIT']:
 rx=r'@"('+prefix+r'[^\n]*?)\\n"';records=re.findall(rx,log);assert records==re.findall(rx,parent),prefix;counts[prefix]=len(records)
raw=re.findall(r'@"(PREEDGE_WRITE_GUARD[^\n]*?)\\n"',log);assert len(raw)==9;rows=[]
for text in raw:
 row={'cycle':int(re.search(r'cycle=\s*(\d+)',text).group(1))};row.update(dict(re.findall(r'([a-z_][a-z_0-9]*)=([01xz])(?:\s|$)',text)));rows.append(row)
assert [r['cycle'] for r in rows]==list(range(9))
parent_audit=json.load(open(B/'native_commit_audit.json'));pending=parent_audit['results']['dbus']['rows'];checks=[]
for r in rows:
 values=[r['native_high'],r['guard'],r['native_done']];possible={int(done or (not high and guard)) for high,guard,done in itertools.product(*[([int(v)] if v in '01' else [0,1]) for v in values])};pred=str(next(iter(possible))) if len(possible)==1 else 'x';assert r['native_we']==pred
 if r['src_high']=='0':
  source='1'
  if r['src_suppress']=='1':source='0'
  if r['src_done']=='1':source='1'
  assert r['src_we']==source
 if r['cycle']>0:assert pending[r['cycle']]['we']==rows[r['cycle']-1]['native_we']
 checks.append({'cycle':r['cycle'],'native_compatible_binary_outputs':sorted(possible),'native_oracle_matches':True,'pending_phase_matches_previous_request':r['cycle']>0})
out={'rows':rows,'checks':checks,'original_record_fidelity':True,'matched_counts':counts,'functional_admission':False,'scope':'Actual nine pre-edge observations and one-cycle native pending correspondence. Procedural source unknown-condition handling differs from conservative binary-cover X propagation; not a binary hardware counterexample or Full equivalence repair.','bindings':{str(f):sha(f) for f in [Path(__file__),P/'protocol.json',P/'control.log',P/'stages.json',B/'native_commit_audit.json']}};(P/'preedge_guard_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(rows[:2],indent=2))
