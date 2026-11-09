"""Actual original bank read and two-slice wrapper state boundary inventory."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];files=[R/'experiments/full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json',R/'experiments/full_ram_mapping_candidate_v1_2026-10-09/structural.json'];mods=[max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m['cells'])) for f in files];s,n=mods;name='IBusCachedPlugin_cache.fetchStage_read_banksValue_0_data';sq=s['netnames'][name]['bits'];nq=n['netnames'][name]['bits'];reg=next(c for c in s['cells'].values() if c['connections'].get('Q')==sq);assert reg['type']=='$dff' and reg['connections']['CLK']==[254];assert not any('init' in v.get('attributes',{}) for v in s['netnames'].values() if any(b in sq for b in v['bits']))
drivers=lambda m:{b:(k,c,port,i) for k,c in m['cells'].items() for port,bits in c['connections'].items() if c['port_directions'][port]=='output' for i,b in enumerate(bits) if isinstance(b,int)}
sd,nd=drivers(s),drivers(n);source=[];struct=[]
for lane,b in enumerate(sq):
 d=reg['connections']['D'][lane];k,c,port,idx=sd[d];assert c['type']=='$mux' and c['connections']['A'][idx]==b
 source.append({'lane':lane,'D':d,'hold_mux':k,'capture_control':c['connections']['S'],'capture_data':c['connections']['B'][idx]})
for lane,b in enumerate(nq):
 k,c,port,i=nd[b];assert c['type']=='$mux';er=c['connections']['S'][0];held=c['connections']['A'][i];inner=c['connections']['B'][i];ik,ic,ip,ii=nd[inner];assert ic['type']=='$mux';raw=ic['connections']['A'][ii];fwd=ic['connections']['B'][ii];hit=ic['connections']['S'][0]
 _,erc,_,eri=nd[er];assert erc['connections']['CLK']==[254];aliases=[{'name':nn,'attributes':v.get('attributes',{})} for nn,v in n['netnames'].items() if er in v['bits']];assert any(v['attributes'].get('init')=='0' for v in aliases)
 struct.append({'lane':lane,'q':b,'outer_mux':k,'er':er,'er_register':erc,'held':held,'hit':hit,'fwd':fwd,'raw':raw,'inner_mux':ik,'er_aliases':aliases})
assert len({tuple(r['capture_control']) for r in source})==1;assert len({r['er'] for r in struct})==2
mem=[{'cell':k,'definition':c} for k,c in s['cells'].items() if c['type'].startswith('$mem') and 'banks_0' in str(c.get('parameters',{}))]
out={'source_read_register':reg,'source_lanes':source,'structural_lanes':struct,'original_memory_cells':mem,'conclusion':'Original32bank read Q is unreset/uninitialized capture/hold state; mapped32visible bits use two delayed slices with er init0 and raw/hit/fwd/held selection. er init0 does not initialize held or source Q.','scope':'Exact payload/state inventory only; no array overwrite coverage, read-oracle equivalence, wrapper clock-order or global admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
D=R/'experiments/full_ibus_bank_read_boundary_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'source_lanes':len(source),'wrapper_lanes':len(struct),'memory_cells':len(mem),'conclusion':out['conclusion']}))
