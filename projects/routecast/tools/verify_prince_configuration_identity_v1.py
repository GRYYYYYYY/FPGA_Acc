"""All resolved fields and launcher profile mutation/relocation contracts."""
import json,re,struct,copy
from pathlib import Path
from pre_route_endpoints import sha
from prince_configuration_identity_v1 import profile
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_configured_consumer_trial_v1_2026-10-20'
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());pp=D/'protocol.json';plan=json.loads(pp.read_text());jobs={j['case']:j for j in plan['jobs']};types=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/base/vpr_types.h';text=types.read_text();fields={}
 for name,count in [('t_router_opts',66),('t_analysis_opts',11)]:
  body=text.split('struct '+name+' {',1)[1].split('\n};',1)[0];body=re.sub(r'//[^\n]*','',body);names=[]
  for declaration in body.split(';'):
   declaration=declaration.strip()
   if declaration:names.append(declaration.split('=',1)[0].split()[-1])
  assert len(names)==count;fields[name]=names
 required={'width_fac','flat_argument'}|{name+'.'+field for name,names in fields.items() for field in names};bindings={str(q):sha(q) for q in [vp,pp,types,Path(__file__),R/'tools/prince_configuration_identity_v1.py']};rows=[];bywidth={}
 for row in v['rows']:
  case=row['case'];d=D/case;resolved=d/'callback.tsv.resolved.tsv';digest=d/'callback.tsv.resolved.sha256';assert digest.read_text().splitlines()==[sha(resolved)];lines=resolved.read_text().splitlines();assert lines[0]=='ROUTECAST_NATIVE_RESOLVED_CONFIGURATION_V1';values={}
  for line in lines[1:]:
   key,kind,payload=line.split('\t');assert key not in values and kind in ['integer','f32','bytes'];values[key]=(kind,payload)
   if kind=='integer':int(payload)
   elif kind=='f32':bits=int(payload);assert 0<=bits<2**32;struct.unpack('<f',struct.pack('<I',bits))
   else:bytes.fromhex(payload)
  assert set(values)==required and len(values)==79;w=int(case.split('/')[0][1:]);assert values['width_fac']==('integer',str(w)) and values['flat_argument']==('integer','0') and values['t_router_opts.max_router_iterations']==('integer','100') and values['t_router_opts.save_routing_per_iteration']==('integer','0')
  payload,launch=profile(jobs[case]['command'],d/'design.blif');assert (d/'launch_configuration.json').read_text()==json.dumps(payload,sort_keys=True,separators=(',',':'));assert (d/'identity.txt').read_text().splitlines()[-1]==launch
  pair=(launch,sha(resolved));bywidth.setdefault(w,set()).add(pair);rows.append(dict(case=case,native_fields=79,launch_SHA256=launch,resolved_SHA256=sha(resolved)))
  for q in [resolved,digest,d/'launch_configuration.json',d/'identity.txt']:bindings[str(q)]=sha(q)
 assert len(bywidth)==3 and all(len(x)==1 for x in bywidth.values()) and len({next(iter(x)) for x in bywidth.values()})==3
 # Independent known-byte fixture: conservative digest changes for every option value.
 fixtures=D/'configuration_fixtures';fixtures.mkdir();arch=fixtures/'architecture.xml';arch.write_text('<architecture/>\n');blif=fixtures/'design.blif';blif.write_text('.model t\n.end\n');cmd=plan['jobs'][0]['command'].copy();cmd[1]=str(arch);base,basehash=profile(cmd,blif);negative=[]
 for flag,new in [('--seed','2'),('--num_workers','2'),('--max_router_iterations','101'),('--route_chan_width','128')]:
  changed=cmd.copy();changed[changed.index(flag)+1]=new;assert profile(changed,blif)[1]!=basehash;negative.append(flag)
 for flag,new in [('--pres_fac_mult','1.4'),('--initial_pres_fac','0.75'),('--acc_fac','1.5'),('--base_cost_type','demand_only')]:
  assert flag not in cmd;changed=cmd+[flag,new];assert profile(changed,blif)[1]!=basehash;negative.append(flag)
 moved=cmd.copy()
 for flag in ['--read_rr_graph','--net_file','--place_file','--route_file']:moved[moved.index(flag)+1]='relocated/'+flag[2:]
 assert profile(moved,blif)[1]==basehash
 arch.write_text('<architecture changed="1"/>\n');assert profile(cmd,blif)[1]!=basehash;arch.write_text('<architecture/>\n');blif.write_text('.model changed\n.end\n');assert profile(cmd,blif)[1]!=basehash
 assert all(sha(q)==h for q,h in bindings.items());(D/'configuration_verification_v1.json').write_text(json.dumps(dict(rows=rows,native_fields_per_route=79,route_entries=18,consistent_configuration_profiles=len(bywidth),option_changes_distinguished=negative,architecture_and_circuit_change_distinguished=True,path_relocation_invariance=True,bindings=bindings,scope='Launcher digest normalizes known file path roles, binding architecture/circuit bytes; graph/net/place/binary hash identities separate. Native route entry independently serializes all66 router+11 analysis fields and width/flat (79). One entry each, digest recomputed from exact text in Python. Distinct option fixtures do not execute alternate routing configurations or prove restart/RNG state persistence. Defaults/options outside these structs are covered only by supplied argv, pinned binary and frozen launch environment.'),indent=2)+'\n');print('CONFIGURATION_IDENTITIES_PASS',len(rows),len(required),negative)
if __name__=='__main__':main()
