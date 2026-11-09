"""Two deterministic same-type placement swaps, no native-route input."""
import json,time,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha,extract
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_swap_candidates_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_comb_only_route_v1_2026-10-09';net=B/'design.net';place=B/'design.place';graph=B/'rr_graph.xml';baseline=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json'
root=ET.parse(net).getroot();types={b.get('name'):b.get('instance').split('[')[0] for b in root.findall('block')}
lines=place.read_text().splitlines();positions={};line_index={}
for i,line in enumerate(lines):
 w=line.split()
 if len(w)>=6 and w[0] in types:positions[w[0]]=tuple(map(int,w[1:5]));line_index[w[0]]=i
assert set(positions)==set(types)
clbs=sorted(n for n in positions if types[n]=='clb');assert len(clbs)>3
anchor=clbs[0];pa=positions[anchor]
partners=sorted(clbs[1:],key=lambda n:(sum(abs(a-b) for a,b in zip(pa[:2],positions[n][:2])),n))[:2]
assert all(positions[n][2:]==pa[2:] for n in partners)
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py',net,place,graph,baseline]}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,anchor=anchor,partners=partners,rule='Lexicographically first packed clb name; nearest two other clbs by Manhattan distance then name; both candidates evaluated, no target data or stop-first-success',scope='Same-type occupied CLB position swaps. Structural candidate validity only; native placement/routing legality and functional admission remain separate.'),indent=2)+'\n')
base=json.loads(baseline.read_text());excluded={row['net_id'] for row in base['comb_constant_global_policy']['excluded_nets']};old={c['connection_id']:c for c in base['connections']};results=[]
for i,partner in enumerate(partners,1):
 folder=D/f'candidate_{i}';folder.mkdir();newlines=list(lines)
 for name,pos in [(anchor,positions[partner]),(partner,pa)]:
  words=lines[line_index[name]].split();words[1:5]=map(str,pos);newlines[line_index[name]]='\t'.join(words)
 candidate=folder/'design.place';candidate.write_text('\n'.join(newlines)+'\n');t=time.perf_counter();ep,report=extract(net,candidate,graph)
 ep['connections']=[c for c in ep['connections'] if c['net_id'] not in excluded];ep['comb_constant_global_policy']=base['comb_constant_global_policy'];assert len(ep['connections'])==16819
 affected=[]
 for c in ep['connections']:
  prior=old[c['connection_id']];assert c['net_id']==prior['net_id']
  if (c['source'],c['sink'])!=(prior['source'],prior['sink']):affected.append(c['connection_id'])
 (folder/'endpoints.json').write_text(json.dumps(ep)+'\n');(folder/'mapping.json').write_text(json.dumps(report)+'\n')
 results.append(dict(candidate=i,swapped=[anchor,partner],affected_connections=affected,extraction_s=time.perf_counter()-t,place_sha256=sha(candidate),endpoint_sha256=sha(folder/'endpoints.json')))
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,scope='Candidate inputs only, no native route outcomes or predictor decisions yet.'),indent=2)+'\n');print([(x['candidate'],x['swapped'],len(x['affected_connections'])) for x in results],flush=True)
