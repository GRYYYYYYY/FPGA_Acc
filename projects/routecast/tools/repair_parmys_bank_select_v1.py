"""Opt-in cloned output-cone repair; original mapping and vendor untouched."""
import copy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/standard_parmys_ram_mapping_v2_2026-10-21';D=R/'experiments/parmys_registered_bank_select_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);protocol={'bindings':{str(p):sha(p) for p in [Path(__file__),P/'dp13x32/mapped.json',P/'dp16x36/mapped.json']},'scope':'Isolated JSON prototype; clone only read-output combinational cones using positive-edge bank samples. RAM/write-enable/clock/reset nets unmodified. No initial/reset values added. Not full-source or architecture admission.'};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for name,a,w in [('dp13x32',13,32),('dp16x36',16,36)]:
  f=D/name;f.mkdir();design=json.loads((P/name/'mapped.json').read_text());m=design['modules']['probe'];original=copy.deepcopy(m);cells=m['cells'];ports=m['ports'];bankbits=a-11;top=max(b for c in cells.values() for bs in c['connections'].values() for b in bs if isinstance(b,int))+1
  def allocate(n):
   nonlocal top
   out=list(range(top,top+n));top+=n;return out
  d=[ports[f'addr{p}~{i}']['bits'][0] for p in [1,2] for i in range(bankbits)];q=allocate(len(d));replacements=dict(zip(d,q));drivers={b:(n,c) for n,c in original['cells'].items() if c['type']!='dual_port_ram' for b in c['connections']['Y']};done={};cloned=[]
  def clonebit(b):
   if b in replacements:return replacements[b]
   if b not in drivers:return b
   n,c=drivers[b]
   if n not in done:
    z=copy.deepcopy(c);assert c['type'] in ['$and','$reduce_or','$reduce_and','$logic_not'];ys=allocate(len(c['connections']['Y']));done[n]=dict(zip(c['connections']['Y'],ys));z['connections']['Y']=ys
    for k in ['A','B']:
     if k in z['connections']:z['connections'][k]=[clonebit(x) for x in c['connections'][k]]
    newname='$routecast_readclone$'+str(len(cloned));assert newname not in cells;cells[newname]=z;cloned.append(newname)
   return done[n][b]
  for k,p in ports.items():
   if p['direction']=='output':p['bits']=[clonebit(b) for b in p['bits']]
  cells['$routecast_bank_sample']={'hide_name':1,'type':'$dff','parameters':{'CLK_POLARITY':'1','WIDTH':format(len(d),'032b')},'attributes':{},'port_directions':{'CLK':'input','D':'input','Q':'output'},'connections':{'CLK':ports['clk']['bits'],'D':d,'Q':q}}
  for n,c in original['cells'].items():assert cells[n]==c
  for k,p in original['ports'].items():
   if p['direction']=='input':assert ports[k]==p
  for k,p in ports.items():
   if k in m.get('netnames',{}):m['netnames'][k]['bits']=p['bits']
  (f/'repaired.json').write_text(json.dumps(design)+'\n');rows.append({'case':name,'sampled_bank_bits':len(d),'cloned_gates':len(cloned),'original_cells_unchanged':True,'repaired_sha256':sha(f/'repaired.json')})
 (D/'repair_manifest.json').write_text(json.dumps({'rows':rows},indent=2)+'\n');print(rows)
if __name__=='__main__':main()
