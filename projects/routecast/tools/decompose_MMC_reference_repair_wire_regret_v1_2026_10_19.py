"""All-NET wire regret attribution under pre-existing changed-endpoint partition."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from array import array
from audit_native_route import NET,NODE
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19';protocol=json.loads((M/'protocol.json').read_text());common=json.loads((M/'common_context.json').read_text());graph=pathlib.Path(common['graph']);assert sha(graph)==common['graph_sha256'];spans=array('I');stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   assert int(e.get('id'))==len(spans);loc=e.find('loc');kind=e.get('type');spans.append(int(loc.get('xhigh'))-int(loc.get('xlow'))+1 if kind=='CHANX' else (int(loc.get('yhigh'))-int(loc.get('ylow'))+1 if kind=='CHANY' else 0));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(spans)==904438
 def pernet(route,names):
  result={};name=None;used=set()
  def finish():
   if name in names:
    assert name not in result;result[name]=sum(spans[n] for n in used)
   else:assert not any(spans[n] for n in used)
  with route.open() as f:
   for line in f:
    m=NET.match(line)
    if m:
     finish();name=m[2];used=set()
    n=NODE.match(line)
    if n:used.add(int(n[1]))
  finish();assert set(result)==names;return result
 rows=[];bindings={str(p):sha(p) for p in [graph,M/'protocol.json',M/'independent_verification_v1.json',pathlib.Path(__file__).resolve()]}
 for plan in protocol['cases']:
  case=plan['case'];ep=pathlib.Path(plan['endpoint']);meta=json.loads(ep.read_text());names=set(meta['net_names'].values());assert len(names)==55300;qs={q['connection_id']:q for q in meta['connections']};dirty={meta['net_names'][str(qs[cid]['net_id'])] for cid in plan['changed_CIDs']};C=R/'experiments/mmc_reference_incremental_astar_canonical_v3_2026-10-19'/case;candidate=C/'canonical/design.route';coldroot=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case;cold=coldroot/'cold_canonical/design.route';cp=C/'receipt.json';np=coldroot/'verification.json';cr=json.loads(cp.read_text());nv=json.loads(np.read_text());assert nv['all_native_physical_and_canonical_pass'];assert cr['files'][str(candidate)]==sha(candidate)
  # Cold rows hash-bind the canonical physical routing file directly.
  rp=coldroot/'rows.json';coldrow=json.loads(rp.read_text())[0];assert coldrow['canonical']['files'][str(cold)]==sha(cold)
  a=pernet(candidate,names);b=pernet(cold,names);assert sum(a.values())==cr['wirelength'] and sum(b.values())==coldrow['wirelength'];parts=[]
  for label,subset in [('changed_endpoint_NETs',dirty),('endpoint_unchanged_retained_NETs',names-dirty)]:
   diffs=[a[n]-b[n] for n in subset];parts.append(dict(partition=label,NETs=len(subset),candidate_wire=sum(a[n] for n in subset),cold_wire=sum(b[n] for n in subset),delta=sum(diffs),worse_NETs=sum(v>0 for v in diffs),better_NETs=sum(v<0 for v in diffs),equal_NETs=sum(v==0 for v in diffs)))
  assert sum(x['delta'] for x in parts)==cr['wirelength']-coldrow['wirelength'];rows.append(dict(case=case,candidate_wire=cr['wirelength'],cold_wire=coldrow['wirelength'],delta=cr['wirelength']-coldrow['wirelength'],partitions=parts))
  for p in [ep,candidate,cold,cp,np,rp]:bindings[str(p)]=sha(p)
  print(case,parts,flush=True)
 O=R/'experiments/mmc_reference_repair_wire_regret_v1_2026-10-19';O.mkdir(exist_ok=False);(O/'review.json').open('x').write(json.dumps(dict(status='ALL3_EXACT_NET_UNION_SPAN_REGRET_PARTITIONED',cases=rows,bindings=bindings,scope='Post-hoc attribution on exposed development data only. Fixed changed-endpoint NET partition from original protocol, not tuned. Delta partition is descriptive, not causal: cold reroutes globally and may alter both partitions. No new search or budget tuning, no predictor admission or speed claim.'),indent=2)+'\n')
if __name__=='__main__':main()
