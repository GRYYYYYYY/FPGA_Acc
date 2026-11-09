"""Rebuild added score fields from raw float32 words and source CHANNEL unions."""
import json,struct,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as Q
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_pressure_timing_rankings_v1_2026-10-20'
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};count=0;cache={}
 for row in v['rows']:
  rp=Path(row['rankings']);r=json.loads(rp.read_text());assert sha(rp)==row['sha256'];assert all(sha(p)==h for p,h in r['bindings'].items());case=row['case'];width=case.split('/')[0];oldp=E/'prince_influence_rankings_v1_2026-10-20'/case/'rankings.json';old=json.loads(oldp.read_text());assert all(sha(p)==h for p,h in old['bindings'].items());src=E/'prince_native_source_checkpoints_v1_2026-10-20'/width/'initial.json';graph=E/'prince_native_cohort_v1_2026-10-20'/width/'source/rr_graph.xml';resourcesp=E/'prince_quality_domains_v1_2026-10-20'/width/'resources.jsonl'
  if width not in cache:
   dest=array('I')
   for ev,x in ET.iterparse(graph):
    if x.tag=='edge':dest.append(int(x.get('sink_node')))
    x.clear()
   resources={x['id']:len(x['bins']) for x in map(json.loads,resourcesp.open())};sets=defaultdict(set)
   for x in json.loads(src.read_text())['records']:sets[x['net_id']].update(dest[e] for e in x['answer']['physical_edge_ids'] if dest[e] in resources)
   cache[width]=(sets,resources)
  sets,resources=cache[width];tp=E/'prince_frame_timings_v1_2026-10-20'/case/'initial_connection_criticalities.json';sp=E/'prince_frame_timings_v1_2026-10-20'/width/'source/initial_connection_criticalities.json'
  def decoded(p):
   out={}
   for x in json.loads(p.read_text()):
    value=struct.unpack('<f',int(x['criticality_bits'],16).to_bytes(4,'little'))[0];q=Q(*value.as_integer_ratio());assert q==Q(x['criticality_numerator'],x['criticality_denominator']);cid=x['connection_id'];assert cid not in out;out[cid]=(x['endpoint_net_id'],q)
   return out
  current=decoded(tp);previous=decoded(sp);cvals=defaultdict(list);dvals=defaultdict(list)
  for cid,(net,value) in current.items():assert previous[cid][0]==net;cvals[net].append(value);dvals[net].append(abs(value-previous[cid][1]))
  for text,scores in r['scores'].items():
   net=int(text)
   for field,value in old['scores'][text].items():assert scores[field]==value
   visits=sum(resources[n] for n in sets[net]);length=len(sets[net]);c=max(cvals[net]);d=max(dvals[net]);expected=dict(delta_total=Q(*scores['delta_mean'])*visits,exposure_total=Q(*scores['exposure_mean'])*visits,criticality_max=c,criticality_delta_max=d,length_criticality=length*c,length_criticality_delta=length*d)
   for field,value in expected.items():assert Q(*scores[field])==value;count+=1
  for p in [rp,oldp,src,graph,resourcesp,tp,sp]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'independent_score_verification_v1.json').write_text(json.dumps(dict(status='ALL_ADDED_SCORE_FIELDS_RAW_FLOAT32_AND_CHANNEL_VISITS_REBUILT',added_score_fields=count,bindings=bindings,scope='Six added fields reconstructed using raw float32 words, CID grouping and source CHANNEL unions/visits. Original five score fields exactly match prior admitted score files. Not label quality or physical timing evidence.'),indent=2)+'\n');print('EXTRA_SCORE_FIELDS_VERIFIED',count)
if __name__=='__main__':main()
