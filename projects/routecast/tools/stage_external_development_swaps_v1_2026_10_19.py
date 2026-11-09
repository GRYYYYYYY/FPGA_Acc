"""Freeze three input-only swaps and validate native placed contexts; no routes."""
import json,itertools,xml.etree.ElementTree as ET,subprocess,resource,time,shlex
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha,physical_maps,placements,extract
from prospective_layout_swap_apply_v1 import make_episodes
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_development_swaps_v1_2026-10-19';out.mkdir(exist_ok=False);source=R/'experiments/prospective_external_family_development_place_v1_2026-10-19';place=source/'source.place';net=source/'design.net';ep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';e=read(ep);graph=Path(e['inputs']['graph']['path']);bundle=R/'experiments/prospective_external_family_prediction_input_bundle_v1_2026-10-19/verification.json';b=read(bundle);assert all(sha(p)==h for p,h in b['bindings'].items());draftp=R/'experiments/prospective_external_family_concrete_cohort_draft_v1_2026-10-18/draft.json';draft=read(draftp);assert draft['proposed_width_cohort']==[96,128,160];native=R/'experiments/prospective_external_family_preroute_context_v2_2026-10-19';np=native/'protocol.json';prior=read(np);assert all(sha(p)==h for p,h in prior['bindings'].items());bindings={str(p):sha(p) for p in [place,net,ep,graph,bundle,draftp,np,Path(__file__).resolve(),R/'tools/prospective_layout_swap_selection_v1.py',R/'tools/prospective_layout_swap_apply_v1.py']};protocol=dict(status='FIXED_INPUT_ONLY_DEVELOPMENT_SWAP_PREPARATION',bindings=bindings,width_roles=[96,128,160],episodes=3,selection='Source CLBs sorted by exact block name. First3disjoint name-ordered pairs at distinct locations with identical full RR physical tile type and subtile; each independently swapped from same source, no chained optimization. Preserve all unavailable/failed episodes; no outcome-based replacement.',execution='This stage validates width128 placed contexts and extracts endpoints only, all native route trees empty. Width96/160 graph/preparation and full predictor/control commands remain incomplete; this is NOT a frozen executable prediction/utility cohort.',family_history='UNKNOWN, development role only, no strict unseen assignment.',no_source_or_target_routing=True);(out/'protocol.json').write_text(json.dumps(protocol,indent=2));types,grid,_=physical_maps(graph);locations=placements(place,sha(net));blocks=[]
 for node in ET.parse(net).getroot().findall('block'):
  name=node.get('name');x,y,sub,layer,bid=locations[name];tid,wo,ho=grid[x,y,layer];assert wo==ho==0;blocks.append(dict(name=name,logical_type=node.get('instance').split('[')[0],location=[x,y,sub,layer],physical_type=types[tid]['name'],subtile=sub))
 result=make_episodes(blocks,3);assert result['selection']['selected']==3;eligible=sorted((a for a in blocks if a['logical_type']=='clb'),key=lambda a:a['name']);used=set();independent=[]
 for a,c in itertools.combinations(eligible,2):
  if a['name'] in used or c['name'] in used or (a['physical_type'],a['subtile'])!=(c['physical_type'],c['subtile']):continue
  independent.append([a['name'],c['name']]);used.update([a['name'],c['name']])
  if len(independent)==3:break
 assert independent==[s['blocks'] for s in result['selection']['swaps']];(out/'selection.json').write_text(json.dumps(result['selection'],indent=2));original=place.read_text().splitlines(keepends=True);source_byname={a['name']:a for a in blocks};plans=[]
 for episode in result['episodes']:
  case=f'episode_{episode["episode"]:02d}';d=out/case;d.mkdir();target=d/'design.place';byname={a['name']:a for a in episode['blocks']};changed=set(episode['changed_blocks']);lines=[]
  for line in original:
   t=line.split()
   if t and t[0] in changed:row=byname[t[0]];lines.append(t[0]+'\t'+'\t'.join(map(str,row['location']))+'\t'+t[5]+'\n')
   else:lines.append(line)
  target.write_text(''.join(lines));newloc=placements(target,sha(net));assert set(newloc)==set(locations);assert {tuple(v[:4]) for v in newloc.values()}=={tuple(v[:4]) for v in locations.values()};assert {name for name in locations if newloc[name]!=locations[name]}==changed
  cmd=list(prior['command']);cmd[1]=str(d/'native_terminals.txt');cmd[cmd.index('--place_file')+1]=str(target);i=cmd.index('--write_rr_graph');del cmd[i:i+2];cmd+=['--read_rr_graph',str(graph)];plans.append(dict(case=case,changed_blocks=sorted(changed),place=str(target),command=cmd,place_sha256=sha(target)))
 (out/'execution_protocol.json').write_text(json.dumps(dict(parent_protocol_sha256=sha(out/'protocol.json'),selection_sha256=sha(out/'selection.json'),jobs=plans,route_search_invoked=False),indent=2));rows=[]
 for plan in plans:
  d=out/plan['case'];tick=time.perf_counter()
  def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
  with (d/'native.log').open('x') as log:run=subprocess.run(plan['command'],cwd=d,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  if run.returncode!=0:
   (out/'failure.json').write_text(json.dumps(dict(case=plan['case'],exit_code=run.returncode,retained_no_replacement=True),indent=2));raise RuntimeError('native target placement load failed; preserved')
  text=(d/'native.log').read_text();assert 'PREROUTE_CONTEXT_EXPORTED_NO_ROUTE_TREES' in text and 'Completed placement consistency check successfully.' in text;endpoints,report=extract(net,Path(plan['place']),graph);(d/'endpoints.json').write_text(json.dumps(endpoints,indent=2)+'\n');(d/'mapping_report.json').write_text(json.dumps(report,indent=2)+'\n');assert len(endpoints['connections'])==15616;nativepairs=Counter();native_names=set()
  for line in (d/'native_terminals.txt').read_text().split('\n'):
   if not line:continue
   t=shlex.split(line)
   if t[0]=='H':assert tuple(map(int,t[1:]))==(119878,1048247,5920);continue
   assert t[0]=='N';name=t[2];native_names.add(name);terms=list(map(int,t[7:]));assert len(terms)==int(t[6]);
   if name!='clk':nativepairs.update((name,terms[0],sink) for sink in terms[1:])
  names={int(i):name for i,name in endpoints['net_names'].items()};actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in endpoints['connections']);assert actual==nativepairs and set(names.values())==native_names;before={q['connection_id']:q for q in e['connections']};assert set(before)=={q['connection_id'] for q in endpoints['connections']};affected=[q['connection_id'] for q in endpoints['connections'] if (q['source'],q['sink'])!=(before[q['connection_id']]['source'],before[q['connection_id']]['sink'])];assert not list(d.glob('*.route'));rows.append(dict(case=plan['case'],blocks=509,changed_blocks=plan['changed_blocks'],connections=15616,affected_connections=len(affected),native_load_and_XML_audit_seconds=time.perf_counter()-tick,graph_sha256=sha(graph)));print('DEVELOPMENT_SWAP_INPUT_PASS',plan['case'],len(affected),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());files=[out/'protocol.json',out/'selection.json',out/'execution_protocol.json',*[p for d in out.iterdir() if d.is_dir() for p in d.iterdir() if p.is_file()]];(out/'verification.json').write_text(json.dumps(dict(status='ALL3_FIXED_DEVELOPMENT_SWAPS_NATIVE_PLACEMENT_AND15616_ENDPOINT_MULTISETS_PASS',rows=rows,bindings={str(p):sha(p) for p in files},source_inputs_unchanged=True,full_prediction_utility_protocol_frozen=False,width96_160_inputs_ready=False,new_source_or_target_routes=False,strict_unseen_admitted=False,scope='Input preparation only; independent pair enumeration/native placement legality and XML/native full endpoint multiplicities. No target timing/floor/budget reuse or model/label/utility evaluation.'),indent=2))
if __name__=='__main__':main()
