"""Isolated actual-source graph candidate: change recognized read-MUX controls only."""
import json,copy,hashlib,re,os,subprocess,resource
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'parmys_source_provenance_replay_v1_2026-10-21';D=E/'source_ram_bank_sampling_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);prov=json.loads((P/'verification_v1.json').read_text());bindings={str(p):sha(p) for p in [Path(__file__),P/'verification_v1.json',*[P/r['source']/'instrumented/mapped.json' for r in prov['rows']]]};(D/'protocol.json').write_text(json.dumps({'scope':'Actual-source mapped graph opt-in candidate. Recognized root-named MUX AND controls replaced by positive-edge sampled selectors; per-selector inverse cloned. All original RAM/write/row/clock/reset logic untouched. X padding untouched. Not source equivalence/admission.','bindings':bindings},indent=2)+'\n');reports=[]
 for row in prov['rows']:
  name=row['source'];f=D/name;f.mkdir();design=json.loads((P/name/'instrumented/mapped.json').read_text());m=design['modules'][name];original=copy.deepcopy(m);aliases=defaultdict(list);drivers={}
  for n,v in m['netnames'].items():
   for b in v['bits']:aliases[b].append(n)
  for n,c in m['cells'].items():
   for p,bs in c['connections'].items():
    if c['port_directions'][p]=='output':
     for b in bs:
      if isinstance(b,int):assert b not in drivers;drivers[b]=(n,c)
  nextbit=max(drivers)+1;nextbit=max(nextbit,1+max(b for c in m['cells'].values() for bs in c['connections'].values() for b in bs if isinstance(b,int)))
  def allocate(n):
   nonlocal nextbit
   out=list(range(nextbit,nextbit+n));nextbit+=n;return out
  groupreports=[];changed=set();added=[]
  for idx,g in enumerate(row['groups']):
   if g['address_bits']<=11:continue
   root=g['mapper_memory_root'];matches=lambda s:re.match(re.escape(root)+r'(?=$|[-_^])',s) and '^MUX_2~' in s
   gates=[n for n,c in original['cells'].items() if c['type']=='$and' and any(matches(alias) for b in c['connections']['Y'] for alias in aliases[b])];assert gates
   selectors=set();pairs={}
   for n in gates:
    c=original['cells'][n];z=c['connections'];assert len(z['A'])==len(z['B'])==len(z['Y'])==2;positive,negative=z['A'];nc=drivers[negative][1];assert nc['type']=='$logic_not' and nc['connections']['A']==[positive] and nc['connections']['Y']==[negative];pairs[n]=(positive,negative);selectors.add(positive)
   selectors=sorted(selectors);assert 0<len(selectors)<=2*(g['address_bits']-11);qs=allocate(len(selectors));invs=allocate(len(selectors));replace={p:(q,inv) for p,q,inv in zip(selectors,qs,invs)};clocks={tuple(original['cells'][n]['connections']['clk']) for n in g['descendant_cells']};assert len(clocks)==1;clock=list(next(iter(clocks)));assert any(clock==p['bits'] for p in original['ports'].values() if p['direction']=='input')
   for t,typ,con,par in [('sample','$dff',{'CLK':clock,'D':selectors,'Q':qs},{'CLK_POLARITY':'1','WIDTH':format(len(selectors),'032b')}),('inverse','$not',{'A':qs,'Y':invs},{'A_SIGNED':'0','A_WIDTH':format(len(qs),'032b'),'Y_WIDTH':format(len(qs),'032b')})]:
    n=f'$routecast_bank_{idx}_{t}';assert n not in m['cells'];m['cells'][n]={'hide_name':1,'type':typ,'parameters':par,'attributes':{},'port_directions':{k:('output' if k in ['Q','Y'] else 'input') for k in con},'connections':con};added.append(n)
   for n,(positive,negative) in pairs.items():assert n not in changed;changed.add(n);m['cells'][n]['connections']['A']=list(replace[positive])
   groupreports.append({'source_instance':g['source_instance'],'root':root,'sampled_selector_bits':selectors,'sampled_Q_bits':qs,'inverse_Q_bits':invs,'clock_bits':clock,'read_MUX_AND_cells':gates})
  assert m['ports']==original['ports']
  for n,c in original['cells'].items():
   if n not in changed:assert m['cells'][n]==c
   else:
    before=copy.deepcopy(c);before['connections']['A']=m['cells'][n]['connections']['A'];assert before==m['cells'][n]
  out=f/'candidate.json';out.write_text(json.dumps(design)+'\n');reports.append({'source':name,'banked_groups':groupreports,'changed_read_AND_cells':len(changed),'added_cells':added,'sampled_bit_count':sum(len(g['sampled_selector_bits']) for g in groupreports),'candidate_sha256':sha(out),'unmodified_other_cells':len(original['cells'])-len(changed),'x_padding_unchanged':True})
 (D/'integration_manifest.json').write_text(json.dumps({'rows':reports},indent=2)+'\n');print([(r['source'],r['sampled_bit_count'],r['changed_read_AND_cells']) for r in reports])
 manifest=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());env=os.environ.copy();env['LD_LIBRARY_PATH']=str(Path(manifest['runtime_library']).parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');checks=[]
 for r in reports:
  f=D/r['source'];ys=f/'check.ys';ys.write_text(f'read_json {f/"candidate.json"}\nhierarchy -top {r["source"]}\ncheck -assert\nstat\n')
  with (f/'check.log').open('w') as log:code=subprocess.call([manifest['yosys_binary'],'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
  checks.append({'source':r['source'],'exit_code':code});print('SOURCE_BANK_CANDIDATE_CHECK',r['source'],code,flush=True)
 (D/'structural_checks.json').write_text(json.dumps({'rows':checks},indent=2)+'\n')
if __name__=='__main__':main()
