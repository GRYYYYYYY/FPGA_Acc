"""Independent full XML domain and own/source pressure table verification."""
import json,sys
from pathlib import Path
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_net2_pressure_intervention_v1_2026-10-19';H=E/'prospective_external_family_net85_net2_pressure_handoff_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 protocol=read(D/'protocol.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());ep=read(protocol['cases'][0]['original_manifest_case']['endpoint']);graph=ep['inputs']['graph']['path'];ids=[];parser=expat.ParserCreate();stack=[]
 def start(tag,a):
  if tag=='node' and stack and stack[-1]=='rr_nodes' and a['type'] in ['CHANX','CHANY']:ids.append(int(a['id']))
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(graph,'rb') as f:parser.ParseFile(f)
 assert ids==sorted(set(ids)) and len(ids)==protocol['channels'];rows=[]
 for case in protocol['cases']:
  table={r['id']:r for r in map(json.loads,(H/case['case']/'all_resource_owner_deltas.jsonl').read_text().splitlines())}
  for arm in case['arms']:
   data=[tuple(map(int,x.split())) for x in Path(arm['pressure']).read_text().splitlines()];assert [x[0] for x in data]==ids
   for n,expected,desired in data:
    row=table.get(n,{});target=len(row.get('target_owners',[]));source=len(row.get('source_owners',[]));assert expected==target and desired==(target if arm['arm']=='own_pressure' else source)
   rows.append(dict(case=case['case'],arm=arm['arm'],resources=len(data),nonzero_offsets=sum(a!=b for n,a,b in data)))
 with (D/'independent_input_verification_v1.json').open('x') as f:json.dump(dict(status='ALL6_FULL_XML_CHANNEL_DOMAINS_AND_OWNER_PRESSURE_INPUTS_VERIFIED',rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print(json.dumps(rows))
if __name__=='__main__':main()
