"""Validate frozen replay fidelity and direct pre-edge tag write observations."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_tag_write_override_preedge_trace_v1_2026-10-09';P=E/'full_source_export_startup_native_commit_trace_v22_2026-10-09'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
a=json.loads((D/'preflight.json').read_text())
for name,h in a['original_hashes'].items():assert sha(P/name)==h
for name in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:assert (D/name).read_bytes()==(P/name).read_bytes()
assert (D/'tb.v').read_text()==(P/'tb.v').read_text().replace(' clk=1;#1;compare;',(D/'added_display.txt').read_text()+' clk=1;#1;compare;')
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages),stages
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();assert 'Fatal' not in log
extract=lambda text:re.findall(r'@"([^\n]*?)\\n"',text)
records=extract(log);baseline=extract(parent)
# MI controller timing banners may differ; every original testbench record must match.
prefixes=['BUS_INPUT','COUNTER_CONTROL','PIPE_BOUNDARY','DATA_FLUSH','PIPE_NODE','FLUSH_CONTROL','READ_CONTROL','TAG_READ','TAG_STATE','FILL_STATE','CACHE_STATE','DIFF','IBUS_COVERAGE','ROUTECAST_FULL_COMPARE_DONE','STARTUP_TAG_WRITE','STARTUP_NATIVE_COMMIT']
counts={}
for prefix in prefixes:
 actual=[s for s in records if s.startswith(prefix)];expected=[s for s in baseline if s.startswith(prefix)];assert actual==expected,prefix;counts[prefix]=len(actual)
rx=r'TAG_OVERRIDE_PREEDGE cycle=\s*(\d+) high=([01xz]) override_lut_input=([01xz]) done=([01xz]) incoming=([01xz]) pending=([01xz]) src_high=([01xz]) src_override=([01xz]) src_done=([01xz]) src_we=([01xz])'
rows=[]
keys=['high','override_lut_input','done','incoming','pending','src_high','src_override','src_done','src_we']
for text in records:
 match=re.fullmatch(rx,text)
 if match:rows.append({'cycle':int(match[1]),**dict(zip(keys,match.groups()[1:]))})
assert [r['cycle'] for r in rows]==list(range(512)),len(rows)
witnesses=[r for r in rows if r['high']=='0' and r['done']=='0' and r['override_lut_input']=='x' and r['incoming']=='x' and r['src_high']=='0' and r['src_override']=='x' and r['src_done']=='0' and r['src_we']=='1']
first=rows[0]
out={'replay_fidelity':True,'stages':stages,'matched_baseline_counts':counts,'rows':rows,'first_row':first,'unknown_override_witnesses':witnesses,'functional_admission':False,'scope':'Direct frozen pre-edge exported/source observations. new_n5367 is transformed LUT input, not raw native override7598. Preserved original failing external output record sequence; no binary hardware defect or all-mismatch diagnosis.','hashes':{str(f.relative_to(R)):sha(f) for f in [D/'preflight.json',D/'control.log',D/'stages.json',D/'actual_lut_audit.json',P/'control.log']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'first_row':first,'witness_count':len(witnesses),'first_witness':witnesses[:1],'baseline_diff_count':counts['DIFF'],'functional_admission':False},indent=2))
