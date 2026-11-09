"""Full context parity, including every original exact electrical increment."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from single_parse_rc_endpoint_context_v1 import load_endpoints
from nonzero_rc_endpoint_context import load_endpoints as reference
from source_binding_v2 import closure
from pre_route_endpoints import sha
out=R/'experiments/single_parse_rc_context_contract_v1_2026-10-07';out.mkdir();bindings=closure([Path(__file__)]);rows=[]
for name in ['bigkey','dsip','misex3']:
 ep=R/f'experiments/mcnc_fresh_conversion_resident_v1_2026-10-07/{name}/endpoints.json';a=load_endpoints(ep);b=reference(ep)
 assert a[:2]==b[:2] and a[5]==b[5];assert a[3]==b[3];assert [__import__('xml.etree.ElementTree',fromlist=['tostring']).tostring(n) for n in a[2]]==[__import__('xml.etree.ElementTree',fromlist=['tostring']).tostring(n) for n in b[2]]
 ar,br=a[4],b[4];assert ar.scale==br.scale and ar.increments==br.increments;assert ar.rc.classes==br.rc.classes and ar.rc.node_classes==br.rc.node_classes and ar.rc.switches==br.rc.switches
 assert all(ar.initial(n)==br.initial(n) for n in range(len(a[2])))
 bindings[str(ep)]=sha(ep);bindings[str(a[0])]=sha(a[0]);rows.append({'name':name,'nodes':len(a[2]),'edges':len(a[3]['edge_ids']),'all_CSR_XML_node_class_switch_exact_increment_initial_scale_query_parity_pass':True});print(name,'PASS',flush=True)
 del a,b
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n')
