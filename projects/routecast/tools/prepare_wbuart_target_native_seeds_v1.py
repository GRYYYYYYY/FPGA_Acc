"""All-nine source tree subset conversion; original physical endpoint admission."""
import json,re,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_target_native_seeds_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);boundary=E/'wbuart_source_restart_boundaries_v1_2026-10-20/verification.json';assert read(boundary)['status']=='ALL3_MISSING_NET_INITIAL_DELAYS_AND6_NEGATIVE_SEEDS_RUNTIME_QUALIFIED';W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';sources=read(E/'wbuart_native_sources_v1_2026-10-20/manifest.json');bindings={str(p):sha(p) for p in [Path(__file__),boundary,W]};rows=[]
 for c in read(W)['comparisons']:
  spec=read(c['specification']);ep=read(spec['endpoint']);prior={q['connection_id']:q for q in read(spec['source_frame'])['records']};dirty={q['net_id'] for q in ep['connections'] if (q['source'],q['sink'])!=(prior[q['connection_id']]['source'],prior[q['connection_id']]['sink'])};names={name:int(n) for n,name in ep['net_names'].items()};width=int(c['case'].split('/')[0][1:]);source=next(x for x in sources['cases'] if x['width']==width);route=Path(source['output'])/'output.route';sourceproof=Path(source['output'])/'verification.json';assert read(sourceproof)['bindings'][str(route)]==sha(route);parts=re.split(r'(?=^Net \d+ \()',route.read_text(),flags=re.M);place=Path(ep['inputs']['place']['path']);assert sha(place)==ep['inputs']['place']['sha256'];header=re.sub(r'Placement_ID: SHA256:[0-9a-f]+','Placement_ID: SHA256:'+sha(place),parts[0],count=1);kept=[];keptnets=set();omittedignored=[]
  for block in parts[1:]:
   m=re.match(r'Net\s+(\d+)\s+\((.*?)\)',block);assert m;name=m[2];net=names.get(name)
   if net not in {q['net_id'] for q in ep['connections']}:
    assert not re.search(r'^Node:',block,re.M);omittedignored.append(name);continue
   if net in dirty:continue
   assert net not in keptnets;keptnets.add(net);kept.append(block)
  d=D/c['case'];d.mkdir(parents=True);seed=d/'seed.route';seed.write_text(header+''.join(kept));physical=audit(ep['inputs']['graph']['path'],seed);printed={int(m[1]):m[2] for l in seed.read_text().splitlines() if (m:=NET.match(l))};expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'] if q['net_id'] not in dirty);observed=Counter((printed[q['net_id']],q['source'],q['sink']) for q in physical['connections']);assert observed==expected and physical['overflow_units']==0;assert len(keptnets)==1074-len(dirty);(d/'physical_audit.json').write_text(json.dumps(physical)+'\n');row={'case':c['case'],'seed':str(seed),'endpoint':spec['endpoint'],'source_route':str(route),'dirty_NETs':sorted(dirty),'retained_NETs':len(keptnets),'retained_connections':sum(expected.values()),'omitted_ignored_empty_sections':omittedignored,'target_placement_sha256':sha(place),'full_original_XML_physical_endpoint_capacity_pass':True};rows.append(row)
  for p in [route,sourceproof,Path(spec['source_frame']),Path(spec['endpoint']),place,seed,d/'physical_audit.json']:bindings[str(p)]=sha(p)
  print(c['case'],len(keptnets),sum(expected.values()),flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_TARGET_SEED_SOURCE_SUBSETS_PHYSICAL_ENDPOINT_CAPACITY_PASS','rows':rows,'bindings':bindings,'scope':'Whole dirty NETs removed, complete clean source blocks copied unchanged; header target placement derived from bound placement content hash, no target route used. Empty ignored sections omitted with flags unchanged. Separate independent retained-block/endpoint/graph audit and actual target-native execution pending; not full native continuation or quality acceptance.'},indent=2)+'\n')
if __name__=='__main__':main()
