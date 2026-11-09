"""Re-extract with an input read guard, then separately compare native endpoint multiset."""
import json,csv,sys
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import extract,sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06';work=root/'work/nonzero_rc_ex5p_reference128_2026-10-06';endpoints=json.loads((out/'endpoints.json').read_text());mapping=json.loads((out/'mapping.json').read_text());allowed={str((work/n).resolve()) for n in ('design.net','design.place','rr_graph.xml')}|{str((root/'tools/pre_route_endpoints.py').resolve())};opened=set();guard_active=True

def guard(event,args):
 if guard_active and event=='open' and isinstance(args[0],(str,bytes)):
  path=str(Path(args[0]).resolve());assert path in allowed,'undeclared extraction read: '+path;opened.add(path)
sys.addaudithook(guard)
result,report=extract(work/'design.net',work/'design.place',work/'rr_graph.xml');guard_active=False;assert result==endpoints and report['pin_details']==mapping['pin_details'];assert opened<=allowed
rows=list(csv.DictReader((work/'before_sync.delays.tsv').open(),delimiter='\t'));sources={};native=Counter()
source_nodes={int(n.get('id')) for n in ET.parse(work/'rr_graph.xml').getroot().find('rr_nodes') if n.get('type')=='SOURCE'}
for row in rows:
 if int(row['node']) in source_nodes:
  net=row['name'];assert net not in sources;sources[net]=int(row['node'])
for row in rows:
 if int(row['pin'])>0:native[row['name'],sources[row['name']],int(row['node'])]+=1
predicted=Counter((endpoints['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in endpoints['connections']);assert native==predicted and sum(native.values())==1916 and not endpoints['excluded_nets'];assert all(sha(v['path'])==v['sha256'] for v in endpoints['inputs'].values());assert endpoints['source_sha256']==sha(root/'tools/pre_route_endpoints.py')
(out/'verification.json').write_text(json.dumps({'connections':1916,'native_endpoint_multiset_exact':True,'extraction_reads_guarded':sorted(opened),'native_reference_read_after_extraction_only':True,'excluded_nets':0,'endpoint_sha256':sha(out/'endpoints.json'),'mapping_sha256':sha(out/'mapping.json'),'verifier_sha256':sha(Path(__file__)),'scope':'Builder reads only declared packedNET/place/RR/source provenance under open audit guard; native names/source/sink/multiplicity comparison occurs afterward. No native path/timing used during generation, no predictor candidate or speed/familyholdout proof.'},indent=2)+'\n');print('verified1916 pre-route endpoints; native multiset exact; extraction input reads guarded')
