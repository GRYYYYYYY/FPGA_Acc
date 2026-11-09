"""Classify65 original constant-folded Q bits without assuming their bases."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_original_unoptimized_proc_state_v1_2026-10-09';af=D/'audit.json';mf=D/'source_unoptimized.json';a=json.loads(af.read_text());m=max(json.loads(mf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));groups={}
for r in a['constant_register_alias_rows']:groups.setdefault(r['unoptimized_bit'],[]).append(r)
drivers={b:(name,c,p,bs.index(b)) for name,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)}
consumers=collections.defaultdict(list)
for name,c in m['cells'].items():
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='input':
   for lane,b in enumerate(bs):
    if b in groups:consumers[b].append({'cell':name,'type':c['type'],'port':p,'lane':lane})
records=[]
for b,rows in groups.items():
 r=rows[0];d=r['register_drivers'][0];c=d['definition'];lane=d['lane'];data=c['connections']['D'][lane];constant=r['optimized_constant'];reset=None
 if c['type']=='$adff':
  value=c['parameters']['ARST_VALUE'][-1-lane];reset={'port':c['connections']['ARST'],'polarity':c['parameters']['ARST_POLARITY'],'value':value,'agrees_with_constant':value==constant};assert value==constant and c['connections']['ARST']==[255] and int(c['parameters']['ARST_POLARITY'],2)==1
 driver=drivers.get(data)
 detail=None if driver is None else {'cell':driver[0],'definition':driver[1],'output_port':driver[2],'output_lane':driver[3]}
 records.append({'bit':b,'aliases':[r['name'] for r in rows],'constant':constant,'cell':d,'reset_base':reset,'data_bit':data,'data_driver':detail,'direct_consumers':consumers[b],'classification':'top_reset_value_matches' if reset else 'unreset_capture_or_guard_obligation','external_output_aliases':[name for name,p in m['ports'].items() if p['direction']=='output' and b in p['bits']]})
assert len(records)==65
out={'records':records,'classes':dict(collections.Counter(r['classification'] for r in records)),'direct_data_driver_types':dict(collections.Counter(r['data_driver']['definition']['type'] if r['data_driver'] else 'literal_or_primary' for r in records)),'scope':'Actual cell/reset/D cone/direct consumer inventory.3ARST values agree with optimized constants under observed reset assertion, not all next-state preservation.62 unreset bits need capture/guard/dead proofs; direct consumer existence is not semantic influence proof.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [af,mf]}}
(D/'constant_classes_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['classes','direct_data_driver_types','scope']},indent=2))
