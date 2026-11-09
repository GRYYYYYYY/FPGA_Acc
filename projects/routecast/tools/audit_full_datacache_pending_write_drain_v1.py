import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};records=[]
for n,c in m['cells'].items():
 if c['type']!='dual_port_ram' or not n.startswith('dataCache_1.'):continue
 co=c['connections'];assert co['clk']==[254] and co['we2']==['0'];q=co['we1'][0];fn,ff=drivers[q];assert ff['type']=='$_DFF_P_' and ff['connections']['C']==co['clk'] and ff['connections']['Q']==[q];init=[]
 for alias,net in m['netnames'].items():
  if q in net['bits'] and 'init' in net.get('attributes',{}):
   lane=net['bits'].index(q);value=net['attributes']['init'][-1-lane];init.append({'alias':alias,'lane':lane,'value':value})
 assert init and all(i['value']=='0' for i in init)
 records.append({'macro':n,'actual_macro_cell':c,'pending_Q':q,'incoming_write_D':ff['connections']['D'][0],'actual_pending_cell_name':fn,'actual_pending_cell':ff,'init_aliases':init,'binary_cases':[{'old_pending':old,'current_incoming_write':0,'current_macro_write_enable':old,'next_pending':0,'next_macro_write_enable':0} for old in [0,1]],'scope':'Current input0 empties pending at next binary posedge; old pending1 still commits on this edge. Actual RAM data/address relation and input source correspondence are separate.'})
assert len(records)==6 and len({r['pending_Q'] for r in records})==5
out={'macro_slices':6,'unique_pending_states':5,'records':records,'source_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'scope':'Exact actual native FF-to-macro bindings and zero-init establish conditional one-edge drain after native incoming write0. Does not prove source no-write conditions imply native incoming0, X/Z events, same-cycle quiescence or Full admission.'};D=R/'experiments/full_datacache_pending_write_drain_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'drain_audit.json').write_text(json.dumps(out,indent=2)+'\n');print('Verified6 actual DataCache macro slices /5 pending states, init0 and conditional one-edge drain; current old pending commit retained')
