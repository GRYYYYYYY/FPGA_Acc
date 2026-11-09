"""Actual retained wrapper FF data/clock/init and macro-pin audit."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_wrapper_visible_selectors_v1_2026-10-09/selector_audit.json';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';a=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
d=collections.defaultdict(list)
for name,c in m['cells'].items():
 for p,bs in c['connections'].items():
  if c['port_directions'][p]=='output':
   for b in bs:d[b].append((name,c))
def ff(q,data,clock):
 pairs=d[q];name,c=pairs[0] if len(pairs)==1 else ('',{})
 return {'q':q,'expected_D':data,'cell':name,'type':c.get('type'),'connections':c.get('connections',{}),'passed':c.get('type')=='$_DFF_P_' and c['connections']['D']==[data] and c['connections']['C']==clock}
def inits(q):
 result=[]
 for name,net in m['netnames'].items():
  value=net.get('attributes',{}).get('init')
  if value is None:continue
  for i,b in enumerate(net['bits']):
   if b==q:result.append({'alias':name,'lane':i,'value':value[-1-i]})
 return result
rows=[];controls=[]
for prefix in a['slices']:
 v={x:m['netnames'][prefix+'.'+x]['bits'] for x in ['clk','re','er','pd','fwd','held','q','hit','pw','pa','ra','raw']}
 er=ff(v['er'][0],v['re'][0],v['clk']);er['init_aliases']=inits(v['er'][0]);er['init_zero']=bool(er['init_aliases']) and all(x['value']=='0' for x in er['init_aliases'])
 hit=d[v['hit'][0]][0][1];pw=d[v['pw'][0]][0][1];macro=m['cells'][prefix+'.ram'];co=macro['connections']
 macro_ok=macro['type']=='dual_port_ram' and all(co[p]==bs for p,bs in {'clk':v['clk'],'we1':v['pw'],'we2':['0'],'addr1':v['pa'],'addr2':v['ra'],'data1':v['pd'],'out2':v['raw']}.items())
 control_ok=er['passed'] and er['init_zero'] and all(c['type']=='$_DFF_P_' and c['connections']['C']==v['clk'] for c in [hit,pw]) and bool(inits(v['pw'][0])) and all(x['value']=='0' for x in inits(v['pw'][0])) and macro_ok
 controls.append({'slice':prefix,'er_update':er,'hit_cell':hit,'pw_cell':pw,'macro_pins_equal':macro_ok,'passed':control_ok})
 for r in a['rows']:
  if r['slice']!=prefix:continue
  i=r['lane'];fwd=ff(v['fwd'][i],v['pd'][i],v['clk']);held=ff(v['held'][i],v['q'][i],v['clk']);rows.append({'slice':prefix,'lane':i,'fwd_update':fwd,'held_update':held,'passed':fwd['passed'] and held['passed']})
out={'slices':len(controls),'passed_slices':sum(c['passed'] for c in controls),'retained_lanes':len(rows),'passed_lane_updates':sum(r['passed'] for r in rows),'controls':controls,'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F]},'scope':'Exact actual native FF D/clock pins: fwd captures pd, held captures q, er captures re with init0; pw init0 and hit/pw clock and macro pins checked. No pw/hit D equivalence beyond prior evidence, no initial held/fwd/raw equality, macro event scheduling, ABC/export or Full admission.'}
D=E/'full_native_wrapper_state_updates_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'state_update_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['slices','passed_slices','retained_lanes','passed_lane_updates']},indent=2));assert all(c['passed'] for c in controls) and all(r['passed'] for r in rows)
