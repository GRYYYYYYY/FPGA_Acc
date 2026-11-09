"""Trace actual override dependency to uninitialized refilling state."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';paths=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',E/'full_native_ram_gates_v3_2026-10-09/gates.json'];mods=[max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{}))) for f in paths];records=[]
for label,m in zip(['source','structural','native'],mods):
 name='dataCache_1.stageB_mmuRsp_refilling';net=m['netnames'][name];q=net['bits'];cs=[(cn,c) for cn,c in m['cells'].items() if c['connections'].get('Q')==q];assert len(cs)==1
 init_aliases=[{'name':k,'init':v['attributes']['init']} for k,v in m['netnames'].items() if v['bits']==q and 'init' in v['attributes']];assert not init_aliases
 cn,c=cs[0];assert c['type']==('$_DFF_P_' if label=='native' else '$sdffce')
 assert 'R' not in c['connections'] and 'ARST' not in c['connections']
 records.append({'stage':label,'net':name,'bit':q[0],'cell':cn,'definition':c,'initialization_aliases':init_aliases})
n=mods[2];drivers={b:(cn,c) for cn,c in n['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};cone=[];leaves=set();seen=set()
def walk(b):
 if not isinstance(b,int) or b in seen:return
 seen.add(b)
 if b not in drivers:leaves.add(b);return
 cn,c=drivers[b]
 if 'DFF' in c['type'] or c['type']=='dual_port_ram':leaves.add(b);return
 cone.append({'bit':b,'cell':cn,'definition':c})
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for x in bs:walk(x)
walk(7598);assert 1928 in leaves
D=E/'full_tag_override_refilling_state_v1_2026-10-09';D.mkdir(exist_ok=True)
out={'state_records':records,'native_override_root':7598,'native_override_cells':cone,'native_override_boundary_leaves':sorted(leaves),'conclusion':'Refilling state directly participates in override OR before tag write clear; it has no known initialization or asynchronous architectural reset in actual source/intermediate/native representations. Source inferred SRST is enabled functional capture logic, not a top-level reset pin.','scope':'Actual structural dependency and initialization inventory. Existing first capture confirms overrideX, but which individual leaf is X then remains unobserved. No claim this single leaf explains every unknown override or all42370 output mismatches.','next_observations':['source refilling and four other override operands','native refillingQ1928 and transformed allow LUT inputs','refilling capture enable and functional clear'],'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'state_bits':[r['bit'] for r in records],'native_override_boundary_leaves':sorted(leaves),'scope':out['scope']},indent=2))
