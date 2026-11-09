"""Full SHA original graph arrays, valid boundary and malformed-input parity."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from immutable_xml_expat_audit_v1 import ImmutableExpatAudit
R=Path(__file__).resolve().parents[1];D=R/'experiments/immutable_expat_full_sha_contract_v1_2026-10-10';assert not D.exists();D.mkdir();graph=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10/seed/rr/sha1/rr_graph.xml';digest=sha(graph);bindings={str(p):sha(p) for p in [Path(__file__).resolve(),R/'tools/immutable_xml_expat_audit_v1.py',R/'tools/immutable_xml_prediction_audit.py',graph]};times={};objects=[]
for cls in [ImmutableXMLAudit,ImmutableExpatAudit]:
 tick=time.perf_counter();objects.append(cls(graph,digest));times[cls.__name__]=time.perf_counter()-tick
old,new=objects;equal={k:bytes(getattr(old,k))==bytes(getattr(new,k)) for k in ['types','caps','spans']};equal.update({k:bytes(getattr(old.graph.edges,k))==bytes(getattr(new.graph.edges,k)) for k in ['source','destination','switch']});assert all(equal.values()) and old.payload_bytes==new.payload_bytes and old.digest==new.digest;assert ImmutableExpatAudit.verify is ImmutableXMLAudit.verify
node='<node id="0" type="CHANX" capacity="1"><loc xlow="0" xhigh="2" ylow="0" yhigh="0"/></node>';valid='<rr_graph><rr_nodes>'+node+'</rr_nodes><rr_edges><edge src_node="0" sink_node="0" switch_id="0"/></rr_edges></rr_graph>';cases={'valid':valid,'wrong_root':valid.replace('rr_graph','wrong'),'id_gap':valid.replace('id="0" type','id="1" type'),'negative_capacity':valid.replace('capacity="1"','capacity="-1"'),'bad_type':valid.replace('CHANX','BOGUS'),'dangling_arc':valid.replace('sink_node="0"','sink_node="1"'),'negative_arc':valid.replace('src_node="0"','src_node="-1"'),'missing_loc':valid.replace('<loc xlow="0" xhigh="2" ylow="0" yhigh="0"/>',''),'nested_decoy_node':valid.replace('<rr_nodes>','<decoy>'+node+'</decoy><rr_nodes>'),'duplicate_loc_first_wins':valid.replace('</node>','<loc xlow="0" xhigh="99" ylow="0" yhigh="0"/></node>'),'malformed':valid[:-8]};rows=[]
for name,text in cases.items():
 p=D/(name+'.xml');p.write_text(text);results=[]
 for cls in [ImmutableXMLAudit,ImmutableExpatAudit]:
  try:
   obj=cls(p,sha(p));results.append(dict(accepted=True,types=bytes(obj.types).hex(),caps=bytes(obj.caps).hex(),spans=bytes(obj.spans).hex(),edges=[bytes(getattr(obj.graph.edges,k)).hex() for k in ['source','destination','switch']]))
  except (ValueError,TypeError,AttributeError,OverflowError,__import__('xml').etree.ElementTree.ParseError,__import__('xml').parsers.expat.ExpatError):results.append(dict(accepted=False))
 assert results[0]==results[1],name;rows.append(dict(name=name,results=results));bindings[str(p)]=sha(p)
assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,full_graph_equal=equal,node_count=len(old.types),edge_count=len(old.graph.edges),reader_seconds=times,cases=rows,original_verify_body_exact=True,scope='Every SHA original graph node/edge array element byte-equal, malformed and boundary grammar parity, original verify method identity. Single cold-then-candidate local read timing only; no full audit/workflow gain, RC reader unchanged and independent.'),indent=2)+'\n');print('FULL GRAPH PARITY',len(old.types),len(old.graph.edges),times)
