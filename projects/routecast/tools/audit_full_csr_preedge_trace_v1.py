import collections,hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_csr_preedge_trace_v1_2026-10-09';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09'
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:assert (D/n).read_bytes()==(S/n).read_bytes()
assert (D/'tb.v').read_text().replace((D/'added_display.txt').read_text(),'')==(S/'tb.v').read_text()
stages=json.loads((D/'stages.json').read_text());assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
log=(D/'control.log').read_text();done=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert done
rows=[]
for line in log.splitlines():
 if 'CSR_PREEDGE cycle=' not in line:continue
 line=line.replace('\\n',' ');row=dict(re.findall(r'(\w+)=\s*([01xXzZ]+)(?=\s|$)',line));row['cycle']=re.search(r'cycle=\s*(\d+)',line).group(1);rows.append(row)
assert len(rows)==512 and [int(r['cycle']) for r in rows]==list(range(512))
masked=[int(r['cycle']) for r in rows if r['select']=='0'];violations=[int(r['cycle']) for r in rows if r['select']=='0' and set(r['contribution'])!={'0'}];assert not violations
def logic_and(a,b):
 if a=='0' or b=='0':return '0'
 if a==b=='1':return '1'
 return 'x'
overrides=[logic_and(r['execute_valid'],r['execute_csr']) for r in rows]
assert set(overrides)=={'0'}
assert all(r['trap']=='0' for r in rows)
out={'source_csr_override_values':dict(collections.Counter(overrides)),'source_trap_outer_values':dict(collections.Counter(r['trap'] for r in rows)),'unknown_contribution_cycles':[int(r['cycle']) for r in rows if re.search('[xXzZ]',r['contribution'])],'valid_csr_pairs':dict(collections.Counter(r['execute_valid']+'/'+r['execute_csr'] for r in rows)),'cycles':512,'mismatches':int(done.group(1)),'select_values':dict(collections.Counter(r['select'] for r in rows)),'known_zero_select_masked_cycles':masked,'execute_csr_values':dict(collections.Counter(r['execute_csr'] for r in rows)),'trap_privileged_capture_cycles':[int(r['cycle']) for r in rows if r['trap']==r['trap_inner']=='1' and r['priv']=='11'],'csr_selected_write_capture_cycles':[int(r['cycle']) for r in rows if r['select']==r['write_en']=='1'],'rows':rows,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','control.log']},'scope':'Actual pre-edge original-source observations with unchanged complete replay comparison. Known-zero select contribution checked; all source valid-and-CSR overrides and outer trap guards are observed0 pre-edge. These discharge only these source capture paths on this trace. Native controls, all other CSR write sinks, event semantics, global equivalence and complete research admission remain separate.'}
(D/'preedge_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes','known_zero_select_masked_cycles']},indent=2))
