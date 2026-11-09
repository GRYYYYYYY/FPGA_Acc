"""Classify actual paired trap-boundary register reset/init evidence."""
import json,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];af=R/'experiments/full_trap_reset_state_step_bridge_v2_2026-10-09/audit.json';a=json.loads(af.read_text());rows=[];hashes={str(af.relative_to(R)):hashlib.sha256(af.read_bytes()).hexdigest()}
mods={}
for label,rel in [('s','full_original_unoptimized_proc_state_v1_2026-10-09/source_unoptimized.json'),('n','full_native_ram_gates_v3_2026-10-09/gates.json')]:
 f=R/'experiments'/rel;mods[label]=max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m['cells']));hashes[str(f.relative_to(R))]=hashlib.sha256(f.read_bytes()).hexdigest()
for name in a['representations']['s']['named_boundary']:
 row={'signal':name,'sides':{}}
 for label,m in mods.items():
  bits=m['netnames'][name]['bits'];assert len(bits)==1;b=bits[0]
  info={'bit':b}
  if isinstance(b,str):info.update(kind='constant',value=b)
  else:
   found=[(k,c,port,bs.index(b)) for k,c in m['cells'].items() for port,bs in c['connections'].items() if c['port_directions'][port]=='output' and b in bs]
   assert len(found)==1,(label,name,len(found));k,c,port,lane=found[0];info.update(cell=k,definition=c,lane=lane)
   init=[{'alias':n,'init':v['attributes']['init'],'lane':v['bits'].index(b)} for n,v in m['netnames'].items() if b in v['bits'] and 'init' in v.get('attributes',{})];info['init_aliases']=init
   if port=='Q' and c['type']=='$adff':info.update(kind='async_reset_register',reset={'bit':c['connections']['ARST'][0],'polarity':c['parameters']['ARST_POLARITY'],'value':c['parameters']['ARST_VALUE'][-1-lane]})
   elif port=='Q' and c['type'].startswith('$_DFF_') and len(c['type'])==10:
    # Yosys $_DFF_PP0_: positive clock, positive async reset, zero value.
    t=c['type'];info.update(kind='async_reset_register',reset={'bit':c['connections']['R'][0],'polarity':'1' if t[7]=='P' else '0','value':t[8]})
   elif port=='Q' and 'ff' in c['type'].lower():info['kind']='unreset_register'
   else:info['kind']='combinational_boundary'
  row['sides'][label]=info
 s,n=row['sides']['s'],row['sides']['n']
 if s['kind']==n['kind']=='async_reset_register' and s['reset']==n['reset']:
  row['classification']='matching_real_reset_base';row['base']=s['reset']
 elif s['kind']==n['kind']=='constant' and s['value']==n['value']:row['classification']='matching_constant'
 elif 'unreset_register' in [s['kind'],n['kind']]:row['classification']='unreset_history_obligation'
 else:row['classification']='combinational_relation_obligation'
 rows.append(row)
capture_bases=[]
for signal,port in [('CsrPlugin_mip_MTIP','timerInterrupt'),('CsrPlugin_mip_MEIP','externalInterrupt')]:
 row=next(r for r in rows if r['signal']==signal)
 for label,m in mods.items():
  assert row['sides'][label]['definition']['connections']['D']==m['ports'][port]['bits']
  assert row['sides'][label]['definition']['connections'].get('CLK',row['sides'][label]['definition']['connections'].get('C'))==[254]
 capture_bases.append({'signal':signal,'shared_input':port,'conclusion':'Unconditional capture of same top-level input on shared clk254 establishes equality after first known shared rising edge; initial equality is not required.'})
counts=dict(collections.Counter(r['classification'] for r in rows));out={'unconditional_input_capture_bases':capture_bases,'counts':counts,'records':rows,'hashes':hashes,'scope':'Actual one-bit paired boundary direct-driver/reset/init inventory. Matching reset proves base only after actual shared reset; no D preservation or full initial/history equality is inferred from aliases.'}
D=R/'experiments/full_trap_boundary_state_bases_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'counts':counts,'classes':{r['signal']:r['classification'] for r in rows}},indent=2))
