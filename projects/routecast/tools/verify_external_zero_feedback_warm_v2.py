"""Independent original Expat/Fraction zero-RC full forecast audit, overload allowed."""
import json,sys,xml.parsers.expat
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_zero_feedback_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');protocol=read(D/'protocol.json');assert proof['status']=='ALL3_ZERO_FEEDBACK_WARM_FRAMES_COPIED_PENDING_ORIGINAL_XML_AUDIT'
 for x in [proof,protocol]:assert all(sha(p)==h for p,h in x['bindings'].items())
 graph=Path(read(protocol['cases'][0]['endpoint'])['inputs']['graph']['path']);caps=array('I');types=[];us=array('I');vs=array('I');switches=array('I');weights={};stack=[];active={};timings=0
 def start(name,attrs):
  nonlocal timings
  parent=stack[-1] if stack else None;stack.append(name)
  if name=='node' and parent=='rr_nodes':assert int(attrs['id'])==len(caps);caps.append(int(attrs['capacity']));types.append(attrs['type'])
  elif name=='timing' and parent=='node':assert Fraction(attrs['R'])==Fraction(attrs['C'])==0;timings+=1
  elif name=='switch' and parent=='switches':active['switch']=int(attrs['id'])
  elif name=='timing' and parent=='switch':
   assert all(Fraction(attrs.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);value=Fraction(attrs.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;weights[active['switch']]=value.numerator
  elif name=='edge' and parent=='rr_edges':us.append(int(attrs['src_node']));vs.append(int(attrs['sink_node']));switches.append(int(attrs['switch_id']))
 def end(name):assert stack.pop()==name
 parser=xml.parsers.expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
 with graph.open('rb') as f:parser.ParseFile(f)
 assert timings==len(caps);digest=sha(graph);bindings={str(p):sha(p) for p in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json',graph]};rows=[]
 for spec in protocol['cases']:
  case=spec['case'];fp=D/case/'frame.json';frame=read(fp);base=read(spec['base_frame']);ep=read(spec['endpoint']);assert frame['scale']==base['scale']==10**18 and frame['graph_sha256']==base['graph_sha256']==ep['graph_sha256']==digest;assert sha(ep['inputs']['graph']['path'])==digest;qs={q['connection_id']:q for q in ep['connections']};old={r['connection_id']:r for r in base['records']};new={r['connection_id']:r for r in frame['records']};assert len(new)==len(frame['records'])==len(qs)==15616 and set(new)==set(old)==set(qs);assert fp.read_bytes()==Path(spec['warm_frame']).read_bytes()
  unions=defaultdict(set);independent=Counter();parents=defaultdict(dict);changed=set()
  for cid,r in new.items():
   q=qs[cid];assert (r['net_id'],r['source'],r['sink'])==(q['net_id'],q['source'],q['sink']);assert {k:v for k,v in r.items() if k!='answer'}=={k:v for k,v in old[cid].items() if k!='answer'}
   if r!=old[cid]:changed.add(r['net_id'])
   u=r['source'];assert types[u]=='SOURCE' and caps[u]>0;seen={u};value=0;edges=r['answer']['physical_edge_ids'];assert r['answer']['status']=='FOUND' and edges
   for pos,eid in enumerate(edges):
    assert type(eid) is int and 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in seen and caps[v]>0
    if pos<len(edges)-1:assert types[v] not in ['SOURCE','SINK']
    if types[v]!='SINK':assert v not in parents[r['net_id']] or parents[r['net_id']][v]==(u,eid);parents[r['net_id']][v]=(u,eid)
    seen.add(v);value+=weights[switches[eid]];u=v
   assert u==r['sink'] and types[u]=='SINK' and value==r['answer']['delay']<=r['budget_integer'];assert type(r['budget_integer']) is int;unions[r['net_id']].update(seen);independent.update(seen)
  ledger=Counter(node for ns in unions.values() for node in ns);assert len(unions)==5919;assert {int(n):v for n,v in frame['ledger'].items()}==dict(ledger);assert {int(n):v for n,v in frame['independent_connection_ledger'].items()}==dict(independent);overflow=sum(max(0,v-caps[n]) for n,v in ledger.items());assert frame['overflow_units']==overflow;assert ('overflow_nodes' not in frame or frame['overflow_nodes']==sum(v>caps[n] for n,v in ledger.items()));assert frame['eligible_for_legal_route_commit'] is False and frame['history']=={};assert frame['budget_policy']==base['budget_policy'];assert frame['epochs']==read(spec['warm_frame'])['epochs'];assert frame['required_connections']==frame['completed_connections']==len(new);row=dict(case=case,all_CIDs=len(new),NETs=len(unions),changed_NETs=len(changed),fullgraph_overflow=overflow,base_overflow=base['overflow_units'],all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True);rows.append(row)
  for p in [fp,Path(spec['base_frame']),Path(spec['warm_frame']),Path(spec['endpoint'])]:bindings[str(p)]=sha(p)
  print('FULL_FORECAST_OVERLAY_INDEPENDENT_PASS',json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL3_ZERO_FEEDBACK_WARM_ORIGINAL_XML_FRACTION_BUDGETS_AND_BOTH_LEDGERS_VERIFIED',rows=rows,all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,bindings=bindings,scope='All complete frame paths and counters verified; overload is explicitly allowed in forecast, not legally routed or objective-guarded native candidate. Frame bytes, epochs and initial history exactly preserved from original warm state, with no feedback. Existing exposed development inputs only, no quality/utility or full-time success.'),indent=2)+'\n')
if __name__=='__main__':main()
