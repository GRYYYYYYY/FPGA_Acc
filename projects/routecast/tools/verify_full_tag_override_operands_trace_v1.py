"""Validate unchanged replay and expose actual unknown override operands."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_tag_override_operands_trace_v1_2026-10-09';P=E/'full_tag_write_override_preedge_trace_v1_2026-10-09';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
pf=json.loads((D/'preflight.json').read_text())
for name,h in pf['original_hashes'].items():assert sha(P/name)==h
for name in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:assert (D/name).read_bytes()==(P/name).read_bytes()
assert (D/'tb.v').read_text()==(P/'tb.v').read_text().replace(' clk=1;#1;compare;',(D/'added_display.txt').read_text()+' clk=1;#1;compare;')
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
log=(D/'control.log').read_text();parent=(P/'control.log').read_text();assert 'Fatal' not in log
extract=lambda t:re.findall(r'@"([^\n]*?)\\n"',t)
r=extract(log);b=extract(parent);prefixes=['BUS_INPUT','COUNTER_CONTROL','PIPE_BOUNDARY','DATA_FLUSH','PIPE_NODE','FLUSH_CONTROL','READ_CONTROL','TAG_READ','TAG_STATE','FILL_STATE','CACHE_STATE','DIFF','IBUS_COVERAGE','ROUTECAST_FULL_COMPARE_DONE','STARTUP_TAG_WRITE','STARTUP_NATIVE_COMMIT','TAG_OVERRIDE_PREEDGE'];counts={}
for prefix in prefixes:
 actual=[s for s in r if s.startswith(prefix)];expected=[s for s in b if s.startswith(prefix)];assert actual==expected,prefix;counts[prefix]=len(actual)
rows=[]
for text in r:
 if text.startswith('TAG_OVERRIDE_OPERANDS '):
  cycle=re.search(r'cycle=\s*(\d+)',text);values=dict(re.findall(r'(\w+)=([01xz])(?:\s|$)',text));assert set(values)==set(pf['signals']);rows.append({'cycle':int(cycle[1]),**values})
assert [row['cycle'] for row in rows]==list(range(512)),len(rows)
operands=['stageB_consistancyHazard','stageB_mmuRsp_refilling','io_cpu_writeBack_accessError','io_cpu_writeBack_mmuException','io_cpu_writeBack_unalignedAccess']
out={'replay_fidelity':True,'stages':stages,'matched_counts':counts,'rows':rows,'first_row':rows[0],'first_unknown_operands':[name for name in operands if rows[0][name] in 'xz'],'first_known_refilling_cycle':next((row['cycle'] for row in rows if row['stageB_mmuRsp_refilling'] in '01'),None),'functional_admission':False,'scope':'Actual frozen pre-edge observations only. More than one unknown operand may contribute; no binary defect, global equivalence or full-mismatch attribution.','hashes':{str(f.relative_to(R)):sha(f) for f in [D/'preflight.json',D/'control.log',D/'stages.json',P/'control.log']}}
(D/'trace_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['first_row','first_unknown_operands','first_known_refilling_cycle','functional_admission']},indent=2))
