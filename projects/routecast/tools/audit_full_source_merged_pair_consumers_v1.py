import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];F=R/'experiments/full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=max(json.loads(F.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})));pairs=[(2014,2727),(2029,2720),(2025,2656),(2026,2688)];records=[]
for pair in pairs:
 members=[]
 for b in pair:
  consumers=[]
  for n,c in m['cells'].items():
   ports={p:[i for i,x in enumerate(bs) if x==b] for p,bs in c['connections'].items() if c['port_directions'][p]=='input' and b in bs}
   if ports:
    outputs=[x for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for x in bs];aliases=[name for name,v in m['netnames'].items() if not name.startswith('$') and set(outputs)&set(v['bits'])];consumers.append({'cell':n,'type':c['type'],'input_lanes':ports,'output_aliases':aliases,'actual_cell':c})
  top=[{'port':n,'lane':i} for n,p in m['ports'].items() if p['direction']=='output' for i,x in enumerate(p['bits']) if x==b]
  members.append({'source_bit':b,'direct_cell_consumers':consumers,'direct_top_outputs':top})
 records.append({'pair':pair,'members':members})
dead=[x['source_bit'] for r in records for x in r['members'] if not x['direct_cell_consumers'] and not x['direct_top_outputs']];assert dead==[2688]
out={'source_bits_with_no_cell_or_top_consumer':dead,'records':records,'source_sha256':hashlib.sha256(F.read_bytes()).hexdigest(),'scope':'Complete actual direct input-lane and top-output consumer inventory only. Consumer aliases are conservative whole-output labels; no assertion that consumers are masked by stage-valid, or that invalid states are harmless.'};D=R/'experiments/full_source_merged_pair_consumers_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'consumer_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps([{'pair':r['pair'],'members':[{'bit':x['source_bit'],'consumers':len(x['direct_cell_consumers']),'top_outputs':x['direct_top_outputs']} for x in r['members']]} for r in records],indent=2))
