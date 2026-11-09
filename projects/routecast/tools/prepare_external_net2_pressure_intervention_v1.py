"""Freeze all3 own/source pressure pairs before intervention outcomes."""
import json,sys
from pathlib import Path
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';H=E/'prospective_external_family_net85_net2_pressure_handoff_v2_2026-10-19';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';D=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 a=read(H/'independent_verification_v1.json');assert all(sha(p)==h for p,h in a['bindings'].items());v=read(H/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());D.mkdir(exist_ok=False);manifest=read(I/'target_manifest.json');ep=read(manifest['cases'][0]['endpoint']);graph=ep['inputs']['graph']['path'];assert sha(graph)==ep['graph_sha256'];channels=set();stack=[];parser=expat.ParserCreate()
 def start(tag,attrs):
  if tag=='node' and stack and stack[-1]=='rr_nodes' and attrs['type'] in ['CHANX','CHANY']:channels.add(int(attrs['id']))
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(graph,'rb') as f:parser.ParseFile(f)
 bindings={graph:sha(graph),str(H/'verification.json'):sha(H/'verification.json'),str(H/'independent_verification_v1.json'):sha(H/'independent_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};cases=[]
 for c in manifest['cases']:
  case=c['case'];p=H/case/'all_resource_owner_deltas.jsonl';records={r['id']:r for r in map(json.loads,p.read_text().splitlines())};bindings[str(p)]=sha(p);arms=[]
  for arm in ['own_pressure','source_pressure']:
   out=D/case/arm;out.mkdir(parents=True);pp=out/'pressure.tsv'
   with pp.open('x') as f:
    for n in sorted(channels):
     r=records.get(n,{});expected=len(r.get('target_owners',[]));desired=expected if arm=='own_pressure' else len(r.get('source_owners',[]));f.write(f'{n}\t{expected}\t{desired}\n')
   bindings[str(pp)]=sha(pp);arms.append(dict(arm=arm,pressure=str(pp),native_output=str(out/'native')))
  cases.append(dict(case=case,original_manifest_case=c,arms=arms))
 protocol=dict(status='ALL6_PRESSURE_ARMS_INPUTS_FROZEN_BEFORE_INTERVENTION',cases=cases,channels=len(channels),bindings=bindings,policy='At round2 order1 NET2 only, assert ALL expected target CHANNEL occupancies, replace with desired own/source observed preNET2 counts including zeros; native same target tree/timing/history and router policy. Restore saved external offsets after native call, reject negatives and stale/partial domain. Own replay must match final baseline. Source replay is deliberately modified cost pressure, not jointly tree-consistent during call, diagnostic only. No final labels or tuning or percase selection; all3 retained; original quality/full9/family/native utility/time/hardware gates unchanged.')
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print('ALL6_ARMS_FROZEN',len(channels))
if __name__=='__main__':main()
