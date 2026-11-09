"""First compatible CLB pair by block ID, selected without route/quality labels."""
import json,sys,shutil,subprocess,os,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha,placements,physical_maps,extract
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
src=R/'experiments/freecores_rr_only_v1_2026-10-08/xtea';graph=src/'rr_graph.xml';types,grid,_=physical_maps(graph);old=placements(src/'design.place',sha(src/'design.net'))
candidates=[]
for name,pos in sorted(old.items(),key=lambda x:x[1][4]):
 x,y,z,layer,bid=pos;tid,wo,ho=grid[x,y,layer]
 if types[tid]['name']=='clb' and (wo,ho)==(0,0) and (types[tid]['width'],types[tid]['height'])==(1,1):candidates.append((name,pos,tid))
# Freeze selection using geometry only; exclude nine prior studied pairs.
import itertools
from collections import defaultdict
cohort_file=R/'experiments/xtea_placement_feedback_cohort_v2_2026-10-13/protocol.json'
prior_file=R/'experiments/xtea_legal_swap_endpoints_v1_2026-10-13/protocol.json'
cohort=json.loads(cohort_file.read_text());prior=json.loads(prior_file.read_text())
excluded={frozenset(x['pair']) for x in cohort['selected']};excluded.add(frozenset(x[0] for x in prior['selected']))
meta=json.loads(Path(cohort['baseline_endpoint']).read_text());included={q['net_id'] for q in meta['connections']};mapping=json.loads((src/'mapping.json').read_text());nets=defaultdict(set);touches=defaultdict(set)
for pin in mapping['pin_details']:
 if pin['net_id'] in included:nets[pin['net_id']].add(pin['block']);touches[pin['block']].add(pin['net_id'])
def hpwl(pos,ids):
 return sum(max(pos[n][0] for n in nets[k])-min(pos[n][0] for n in nets[k])+max(pos[n][1] for n in nets[k])-min(pos[n][1] for n in nets[k]) for k in ids)
selected=None;examined=0
for first,second in itertools.combinations(candidates,2):
 if first[2]!=second[2] or first[1][2:4]!=second[1][2:4] or frozenset([first[0],second[0]]) in excluded:continue
 examined+=1;a,b=first[0],second[0];newpos={**old,a:(*second[1][:4],first[1][4]),b:(*first[1][:4],second[1][4])};dirty=touches[a]|touches[b];delta=hpwl(newpos,dirty)-hpwl(old,dirty)
 if delta<=0:selected=[first,second];break
assert selected is not None
first,second=selected

D=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18';D.mkdir();W=D/'xtea';W.mkdir();bindings=closure([Path(__file__)]);bindings.update({str(p):sha(p) for p in [cohort_file,prior_file,Path(cohort['baseline_endpoint'])]})
for n in ['design.place','design.net','design.blif','rr_graph.xml','endpoints.json','mapping.json']:bindings[str(src/n)]=sha(src/n)
for n in ['design.net','design.blif']:shutil.copyfile(src/n,W/n)
(W/'rr_graph.xml').symlink_to(graph);changes={first[0]:second[1][:4],second[0]:first[1][:4]};lines=[]
for line in (src/'design.place').read_text().splitlines():
 fields=line.split()
 if fields and fields[0] in changes:fields[1:5]=map(str,changes[fields[0]]);line='\t'.join(fields)
 lines.append(line)
(W/'design.place').write_text('\n'.join(lines)+'\n');new=placements(W/'design.place',sha(W/'design.net'))
assert set(new)==set(old) and all(new[n][4]==old[n][4] for n in old)
assert {n for n in old if new[n]!=old[n]}==set(changes) and {p[:4] for p in old.values()}=={p[:4] for p in new.values()}
binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
for p in [binary,arch,W/'design.place',W/'design.net',W/'design.blif']:bindings[str(p)]=sha(p)
cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--check_route','full']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,selected=selected,changes=changes,command=cmd,excluded_prior_pairs=[sorted(x) for x in sorted(excluded,key=lambda x:sorted(x))],compatible_pairs_examined=examined,hpwl_delta=delta,selection='First compatible unitCLB pair by ascending block ID with physical-demand HPWL delta<=0; exclude the nine explicitly listed prior pairs. No target native/model outputs read; exposed development design, not unseen-family validation.',scope='Exposed XTEA local swap input; no TilePlace live state, no heldout or QoR claim.'),indent=2)+'\n');tick=time.perf_counter()
with (W/'placement_check.log').open('x') as log:code=subprocess.call(cmd,cwd=W,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT)
text=(W/'placement_check.log').read_text();assert code==1 and 'Completed placement consistency check successfully.' in text and 'Cannot open missing.route' in text and not list(W.glob('*.route'))
ep,mapping=extract(W/'design.net',W/'design.place',W/'rr_graph.xml');(W/'endpoints.json').write_text(json.dumps(ep)+'\n');(W/'mapping.json').write_text(json.dumps(mapping)+'\n')
original=json.loads((src/'endpoints.json').read_text());oldmap=json.loads((src/'mapping.json').read_text());assert ep['net_names']==original['net_names'] and ep['excluded_nets']==original['excluded_nets'];assert len(mapping['pin_details'])==len(oldmap['pin_details'])
for a,b in zip(oldmap['pin_details'],mapping['pin_details']):assert {k:v for k,v in a.items() if k!='rr_node'}=={k:v for k,v in b.items() if k!='rr_node'}
a={q['connection_id']:q for q in original['connections']};b={q['connection_id']:q for q in ep['connections']};assert a.keys()==b.keys() and all(a[c]['net_id']==b[c]['net_id'] for c in a)
changed=[cid for cid in a if a[cid]!=b[cid]];assert changed
(D/'endpoint_delta.json').write_text(json.dumps(dict(changed_connection_ids=changed,changed_nets=sorted({a[c]['net_id'] for c in changed}),all_query_count=len(a),old_endpoints=str(src/'endpoints.json'),new_endpoints=str(W/'endpoints.json')),indent=2)+'\n')
assert all(sha(p)==h for p,h in bindings.items())
row=dict(name='xtea',exit_code=code,status='GRAPH_AND_ENDPOINTS_CAPTURED',connections=len(a),graph_sha256=ep['graph_sha256'],native_placement_check_and_extraction_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in W.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=[row],native_route_labels_generated=False),indent=2)+'\n');print('XTEA legal swap',len(changed),'changed of',len(a),'unfiltered connections',flush=True)
