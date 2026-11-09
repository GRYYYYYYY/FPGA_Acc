"""Logging-only plugin build; all outputs local, vendor build inputs read-only."""
import json,hashlib,shlex,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';BUILD=V/'build_tileplace_frontend/parmys';D=R/'experiments/private_parmys_provenance_build_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);src=V/'parmys/parmys-plugin';patches={}
 text=(src/'parmys.cc').read_text();needle='            /*add this node to blif_netlist as an internal node */';assert text.count(needle)==1;text=text.replace(needle,'            if (new_node->type == SPRAM || new_node->type == DPRAM) log("RC_RAM_INPUT\\t%s\\t%s\\n", cell->name.c_str(), new_node->name);\n'+needle);patches['parmys.cc']=text
 text=(src/'core/memory.cc').read_text();text='#include <cstdio>\n'+text
 for token in ['spram','dpram']:
  needle=f'    {token}->name = node_name({token}, hb_name);';assert text.count(needle)==1;text=text.replace(needle,needle+f'\n    fprintf(stderr, "RC_RAM_CREATE\\t%s\\t%s\\n", node->name, {token}->name);')
 patches['memory.cc']=text
 flags=BUILD/'CMakeFiles/parmys.dir/flags.make';linkfile=BUILD/'CMakeFiles/parmys.dir/link.txt';config={}
 for line in flags.read_text().splitlines():
  if ' = ' in line:
   k,v=line.split(' = ',1);config[k]=shlex.split(v)
 cmds=[];localobjects={}
 for name,text in patches.items():
  file=D/name;file.write_text(text);obj=D/(name+'.o');localobjects[name]=obj;cmds.append(['/usr/bin/c++',*config['CXX_DEFINES'],*config['CXX_INCLUDES'],*config['CXX_FLAGS'],'-c',str(file),'-o',str(obj)])
 link=shlex.split(linkfile.read_text());replacements={'CMakeFiles/parmys.dir/parmys-plugin/parmys.cc.o':localobjects['parmys.cc'],'CMakeFiles/parmys.dir/parmys-plugin/core/memory.cc.o':localobjects['memory.cc']};vendorinputs=[]
 for i,x in enumerate(link):
  if x in replacements:link[i]=str(replacements[x])
  elif x.endswith(('.o','.a')):
   p=(BUILD/x).resolve();assert p.exists();link[i]=str(p);vendorinputs.append(p)
 outidx=link.index('-o')+1;link[outidx]=str(D/'parmys_provenance.so');cmds.append(link);bindings={str(p):sha(p) for p in [Path(__file__),src/'parmys.cc',src/'core/memory.cc',flags,linkfile,*vendorinputs]};(D/'protocol.json').write_text(json.dumps({'scope':'Only fprintf/log instrumentation, original behavior unmodified; private objects/shared library and stdout logs only. Vendor sources, objects, archives read-only. Exact map parity must be independently checked.','commands':cmds,'bindings':bindings},indent=2)+'\n');rows=[]
 for i,cmd in enumerate(cmds):
  with (D/f'build_{i}.log').open('w') as f:code=subprocess.call(cmd,cwd=D,stdout=f,stderr=subprocess.STDOUT)
  rows.append({'stage':i,'exit_code':code});print('PRIVATE_PLUGIN_BUILD',i,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
