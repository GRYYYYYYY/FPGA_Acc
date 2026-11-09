import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';A=E/'full_structural_native_datacache_control_steps_v1_2026-10-09/condition_audit.json';B=E/'full_paired_state_native_bridge_obligations_v1_2026-10-09/bridge_obligations.json';I=E/'full_source_structural_initial_obligations_v1_2026-10-09/initial_obligations.json';G=E/'full_native_ram_gates_v3_2026-10-09/gates.json';a=json.loads(A.read_text());m=max(json.loads(G.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));bridge={r['intermediate_bit']:r for r in json.loads(B.read_text())['records']};init={r['source_bit']:r for r in json.loads(I.read_text())['registers']};primary={b:n for n,p in m['ports'].items() if p['direction']=='input' for b in p['bits']};drivers={b:c for c in m['cells'].values() if 'DFF' in c['type'] for b in c['connections']['Q']};reverse=collections.defaultdict(list)
for old,new in a['leafmaps']['structural'].items():reverse[new].append(int(old))
records=[]
for b in a['shared_symbols']:
 if b in primary:records.append({'native_bit':b,'kind':'primary_input','port':primary[b]});continue
 assert b in drivers
 joined=[]
 for old in reverse[b]:
  if old in bridge:
   r=bridge[old];joined.append({'intermediate_bit':old,'source_bit':r['source_bit'],'source_reset_kind':r['source_reset_kind'],'explicit_known_initial_equality':init[r['source_bit']]['explicit_known_initial_equality']})
 records.append({'native_bit':b,'kind':'paired_register' if joined else 'unjoined_register','native_cell':drivers[b],'paired_source_rows':joined,'intermediate_bits':reverse[b],'aliases':[n for n,v in m['netnames'].items() if b in v['bits'] and not n.startswith(('$','_'))]})
counts=dict(collections.Counter(r['kind'] for r in records));out={'symbols':len(records),'counts':counts,'paired_source_reset_kinds':dict(collections.Counter(p['source_reset_kind'] for r in records for p in r.get('paired_source_rows',[]))),'unjoined_native_bits':[r['native_bit'] for r in records if r['kind']=='unjoined_register'],'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A,B,I,G]},'scope':'Exact52-symbol dependency join for proved8 native control steps. Existing source/intermediate step correspondence does not establish all native steps or initial relation; unjoined states retained, not ignored.'};D=E/'full_datacache_control_step_dependencies_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'dependency_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes']},indent=2))
