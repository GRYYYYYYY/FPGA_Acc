"""Classify full boundary and paired-register initial/reset obligations."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_external_output_state_closure_v1_2026-10-09';F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';M=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json';C=P/'mapping_candidates.json';s,m=[max(json.loads(p.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{}))) for p in [F,M]];mapping=json.loads(C.read_text())['records'];pairs=json.loads((P/'register_driver_pairs.json').read_text())['records'];inputs={b for p in s['ports'].values() if p['direction']=='input' for b in p['bits']}
def drivers(mod):return {b:(n,c,p,i) for n,c in mod['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs)}
sd,md=drivers(s),drivers(m)
def inits(mod):
 values=collections.defaultdict(list)
 for n,net in mod['netnames'].items():
  value=net.get('attributes',{}).get('init')
  if value is not None:
   for lane,b in enumerate(net['bits']):values[b].append({'alias':n,'lane':lane,'value':value[-1-lane]})
 return values
si,mi=inits(s),inits(m);classes=[]
for r in mapping:
 b=r['source_bit'];xs=r['mapped_candidates'];source=sd.get(b);mapped=md.get(xs[0]) if len(xs)==1 else None
 if b in inputs:kind='primary_input'
 elif source and source[1]['type'].startswith('$memrd'):kind='raw_memory_read'
 elif len(xs)==1 and isinstance(xs[0],str):kind='constant_invariant'
 elif source and 'dff' in source[1]['type'].lower() and mapped and 'dff' in mapped[1]['type'].lower():kind='paired_register'
 elif source and 'dff' in source[1]['type'].lower() and mapped and mapped[1]['type']=='$mux':kind='ram_visible_state'
 elif source and 'dff' in source[1]['type'].lower() and not mapped:kind='dead_source_state'
 else:kind='unclassified'
 classes.append({'source_bit':b,'kind':kind,'mapped_candidates':xs})
rows=[]
for r in pairs:
 d=r['mapped_driver']
 if not d or 'dff' not in d['type'].lower():continue
 a=s['cells'][r['source_cell']];b=m['cells'][d['cell']];src_lane=r['source_lane'];mapped_lane=d['lane'];assert a['type']==b['type'];kind='asynchronous_reset' if 'ARST' in a['connections'] else 'synchronous_reset_enable_priority' if a['type']=='$sdffce' else 'synchronous_reset_priority' if 'SRST' in a['connections'] else 'no_reset'
 reset_values={}
 for port in ['ARST','SRST']:
  if port in a['connections']:
   key=port+'_VALUE';x=a['parameters'][key][-1-src_lane];y=b['parameters'][key][-1-mapped_lane];assert x==y and a['parameters'][port+'_POLARITY']==b['parameters'][port+'_POLARITY'];reset_values[port]=x
 source_init=si[r['source_bit']];mapped_init=mi[r['mapped_candidates'][0]];source_known={x['value'] for x in source_init if x['value'] in '01'};mapped_known={x['value'] for x in mapped_init if x['value'] in '01'};assert len(source_known)<=1 and len(mapped_known)<=1
 init_equal=bool(source_known) and source_known==mapped_known
 rows.append({'source_bit':r['source_bit'],'mapped_bit':r['mapped_candidates'][0],'type':a['type'],'reset_kind':kind,'reset_values':reset_values,'source_init':source_init,'mapped_init':mapped_init,'explicit_known_initial_equality':init_equal,'reset_base_scope':'Requires actual reset assertion' if kind=='asynchronous_reset' else 'Requires reset and active enable at clock edge' if kind=='synchronous_reset_enable_priority' else 'Requires reset at clock edge' if kind=='synchronous_reset_priority' else 'Requires coupled initial state or independently proven overwrite/nonobservability'})
out={'boundary_classes':dict(collections.Counter(r['kind'] for r in classes)),'paired_reset_classes':dict(collections.Counter(r['reset_kind'] for r in rows)),'paired_register_bits':len(rows),'explicit_known_initial_equal_bits':sum(r['explicit_known_initial_equality'] for r in rows),'classes':classes,'registers':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,M,C,P/'register_driver_pairs.json']},'scope':'Complete boundary and actual reset/init metadata classification. Matching reset values gives a conditional base after qualifying reset events, not proof replay supplies events to all states or no earlier observable effects. Memory arrays/visible states, dead states and kill invariant retain separate proofs; no Full admission.'};D=E/'full_source_structural_initial_obligations_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'initial_obligations.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['boundary_classes','paired_reset_classes','paired_register_bits','explicit_known_initial_equal_bits']},indent=2));assert len(classes)==2218 and len(rows)==1741 and out['boundary_classes'].get('unclassified',0)==0
