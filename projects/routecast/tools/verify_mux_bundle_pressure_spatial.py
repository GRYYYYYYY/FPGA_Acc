"""Independent full XML grouping and rational bundle metric reconstruction."""
import json,math,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_bundle_pressure_spatial_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and len(r['rows'])==9 and r['protocol_sha256']==sha(out/'protocol.json');assert p['source_sha256']==sha(root/'tools/evaluate_mux_bundle_pressure_spatial.py')
def ranks(values):
 return [Fraction(sum(y<x for y in values)*2+sum(y==x for y in values)-1,2) for x in values]
rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert all(sha(f)==h for f,h in c['bindings'].items()) and sha(c['vectors'])==c['vectors_sha256'];vectors=json.loads(Path(c['vectors']).read_text());lookup={x['node']:x for x in vectors};groups=defaultdict(list);xml=ET.parse(c['graph']).getroot()
 for node in xml.find('rr_nodes'):
  i=int(node.get('id'))
  if i not in lookup:continue
  loc=node.find('loc');groups[(node.get('type'),node.get('direction'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']])].append(i)
 expected=[{'key':list(k),'nodes':sorted(ids),**{field:sum(lookup[i][field] for i in ids) for field in ['capacity','predicted','native']}} for k,ids in sorted(groups.items())]
 file=out/f"mux_w{c['data_width']}_c{c['channels']}_bundles.json";assert sha(file)==row['detail_sha256'] and json.loads(file.read_text())==expected
 a=[Fraction(x['predicted'],x['capacity']) for x in expected];b=[Fraction(x['native'],x['capacity']) for x in expected];ra=ranks(a);rb=ranks(b);mean=Fraction(len(a)-1,2);rho=float(sum((x-mean)*(y-mean) for x,y in zip(ra,rb)))/math.sqrt(float(sum((x-mean)**2 for x in ra)*sum((x-mean)**2 for x in rb)));assert math.isclose(rho,row['bundle_rho'],abs_tol=1e-12);assert math.isclose(float(sum(abs(x-y) for x,y in zip(a,b))/len(a)),row['bundle_MAE'],abs_tol=1e-12)
 ps={i for i,x in enumerate(a) if x>1};ts={i for i,x in enumerate(b) if x>1};hit=len(ps&ts);assert row['bundle_overuse']=={'predicted':len(ps),'native':len(ts),'intersection':hit,'precision':hit/len(ps) if ps else None,'recall':hit/len(ts) if ts else None}
 for field in ['predicted','native']:
  assert sum(x[field] for x in vectors)==sum(x[field] for x in expected)
  hidden=sum(max(0,x[field]-x['capacity']) for x in vectors)-sum(max(0,x[field]-x['capacity']) for x in expected);assert hidden==row['hidden_'+field+'_track_overflow'] and hidden>=0
 rows.append({'data_width':c['data_width'],'channels':c['channels'],'bundles_verified':len(expected),'rho':rho});print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'All originalXML grouping/demand/capacity conservation and rationalrank/support metrics verified; aggregation cannot establish legal track routing.'},indent=2)+'\n')
