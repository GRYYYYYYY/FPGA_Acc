"""SAT on actual-source read cones with explicitly abstracted sampled state."""
import json,hashlib,os,subprocess,functools
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'actual_source_bank_cones_sat_v1_2026-10-21';P=E/'source_ram_bank_sampling_v1_2026-10-21';B=E/'parmys_source_provenance_replay_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);manifest=json.loads((P/'integration_manifest.json').read_text());row=next(r for r in manifest['rows'] if r['source']=='mcml');old=json.loads((B/'mcml/instrumented/mapped.json').read_text())['modules']['mcml'];new=json.loads((P/'mcml/candidate.json').read_text())['modules']['mcml'];prov={g['source_instance']:g for g in json.loads((B/'verification_v1.json').read_text())['rows'][0]['groups']};m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'All7 actual source repaired read groups. Physical RAM outputs and sampled bank Q abstract arbitrary binary inputs. Prove original read logic with bank D substituted by sampled Q equals actual repaired logic; negative control keeps live bank D. No complete memory/source/state/collision or four-state proof.','bindings':{str(p):sha(p) for p in [Path(__file__),P/'integration_manifest.json',P/'mcml/candidate.json',B/'mcml/instrumented/mapped.json',B/'verification_v1.json',binary,runtime]}},indent=2)+'\n');results=[]
 def drivers(obj):return {b:c for c in obj['cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)}
 od,nd=drivers(old),drivers(new)
 for idx,g in enumerate(row['banked_groups']):
  physical=prov[g['source_instance']];ramouts={b for n in physical['descendant_cells'] for p,bs in old['cells'][n]['connections'].items() if old['cells'][n]['port_directions'][p]=='output' for b in bs};q=set(g['sampled_Q_bits']);sel=set(g['sampled_selector_bits']);free=ramouts|q|sel;sub=dict(zip(g['sampled_selector_bits'],g['sampled_Q_bits']));targets=[b for n in g['read_MUX_AND_cells'] for b in old['cells'][n]['connections']['Y']]
  for mode in ['repair','unrepaired_negative']:
   f=D/(str(idx)+'_'+mode);f.mkdir();statements=[];names={};counter=0
   def sig(bit,arm):
    nonlocal counter
    if isinstance(bit,str):assert bit in ['0','1'];return "1'b"+bit
    if arm=='reference' and bit in sub:bit=sub[bit]
    if bit in free:return 'i'+str(bit)
    key=(arm,bit)
    if key in names:return names[key]
    drv=od if arm in ['reference','negative'] else nd;c=drv[bit];z=c['connections'];t=c['type'];assert t in ['$and','$reduce_or','$logic_not','$not'];ys=z['Y'];local=['v'+str(counter+i) for i in range(len(ys))];counter+=len(ys)
    for b,n in zip(ys,local):names[arm,b]=n
    def vec(bits):return '{'+','.join(sig(b,arm) for b in reversed(bits))+'}'
    expr=vec(z['A'])+' & '+vec(z['B']) if t=='$and' else {'$reduce_or':'|','$logic_not':'!','$not':'~'}[t]+vec(z['A']);statements.append('wire '+','.join(local)+'; assign {'+','.join(reversed(local))+'} = '+expr+';');return names[key]
   comparisons=[]
   for bit in targets:comparisons.append('('+sig(bit,'reference')+' == '+sig(bit,'candidate' if mode=='repair' else 'negative')+')')
   v=f/'proof.v';v.write_text('module proof('+','.join('input i'+str(b) for b in sorted(free))+',output ok);\n'+'\n'.join(statements)+'\nassign ok = '+' & '.join(comparisons)+';\nendmodule\n');ys=f/'commands.ys';ys.write_text(f'read_verilog {v}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat -verify -prove ok 1 -show ok\n')
   with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT)
   log=(f/'yosys.log').read_text();passed=code==0 and 'no model found: SUCCESS' in log;negative_failed=code==1 and 'proof did fail' in log;results.append({'source_instance':g['source_instance'],'mode':mode,'exit_code':code,'proof_passed':passed,'negative_failed':negative_failed,'compared_bits':len(targets),'RAM_output_free_bits':len(ramouts),'sampled_bank_bits':len(q),'bindings':{str(p.relative_to(R)):sha(p) for p in [v,ys,f/'yosys.log']}});(D/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print(idx,mode,code,passed,negative_failed,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':results},indent=2)+'\n')
if __name__=='__main__':main()
