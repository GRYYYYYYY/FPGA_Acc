"""Full-frame Fraction/path/NET/ledger/objective and all-subset independent replay."""
import sys,json,math,array,collections
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';d=E/'mmc_joint_channel_diamond_v1_2026-10-18';rp=d/'receipt.json';receipt=json.loads(rp.read_text());plan=json.loads((E/'mmc_channel_diamond_Pareto_v1_2026-10-18/protocol.json').read_text());cost=json.loads((E/'mmc_objective_terminal_subset_v1_2026-10-18/protocol.json').read_text());bindings={**receipt['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};results=[]
 with Cache().installed():
  for p,h in bindings.items():assert sha(p)==h
  print('JOINT FULL FRAME AUDIT GRAPH LOAD',flush=True);_,digest,nodes,f,rc,_=load_endpoints(plan['inputs']['case_01']['endpoint']);slots=array.array('I',[0])*len(f['edge_ids'])
  for s,e in enumerate(f['edge_ids']):slots[e]=s
  caps=f['capacities'];span={}
  for n,node in enumerate(nodes):
   if node.get('type') in ['CHANX','CHANY']:
    loc=node.find('loc');span[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  wire=rc.scale//(20*10**9)
  for summary in receipt['summaries']:
   case=summary['case'];inputs=cost['inputs'][case];base,crit,extra=load(plan['inputs'][case]['endpoint'],inputs['node_base_proof'],inputs['criticality_directory'],len(nodes),rc.scale);bindings.update(extra);D=math.lcm(*(v['criticality_denominator'] for v in crit.values()));units={cid:v['criticality_numerator']*(D//v['criticality_denominator']) for cid,v in crit.items()};old=json.loads(Path(plan['inputs'][case]['frame']).read_text());newp=d/case/'candidate.json';new=json.loads(newp.read_text());matrixp=d/case/'subset_matrix.json';matrix=json.loads(matrixp.read_text());assert sha(newp)==summary['files'][str(newp)] and sha(matrixp)==summary['files'][str(matrixp)];assert not old['history'] and new['graph_sha256']==old['graph_sha256']==digest;bycid={r['connection_id']:r for r in old['records']};newcid={r['connection_id']:r for r in new['records']};assert len(bycid)==len(newcid)==115572 and bycid.keys()==newcid.keys();nets=collections.defaultdict(list)
   for cid,row in newcid.items():
    original=bycid[cid];assert {k:v for k,v in row.items() if k!='answer'}=={k:v for k,v in original.items() if k!='answer'};nets[row['net_id']].append(cid)
   def interpret(frame):
    records={r['connection_id']:r for r in frame['records']};ledger=collections.Counter();independent=collections.Counter();weights=collections.Counter();raw=0;pernet={}
    for net,cids in nets.items():
     parent={};users={};netraw=0;source=records[cids[0]]['source']
     for cid in cids:
      row=records[cid];assert row['source']==source and row['answer']['status']=='FOUND';current=source;seen={source};delay=rc.rc.node(source)[0]*rc.rc.node(source)[1]/2
      for edge in row['answer']['physical_edge_ids']:
       assert 0<=edge<len(slots);s=slots[edge];assert f['edge_ids'][s]==edge and f['row_offsets'][current]<=s<f['row_offsets'][current+1];target=f['dest_ranks'][s];assert target not in seen and caps[target]>0;assert target not in parent or parent[target]==(current,edge);parent[target]=(current,edge);seen.add(target);delay+=rc.rc.increment(s);current=target
      assert current==row['sink'] and delay*rc.scale==row['answer']['delay'] and delay<=Fraction(row['budget_integer'],rc.scale);independent.update(seen);netraw+=units[cid]*row['answer']['delay']
      for n in seen:users[n]=max(users.get(n,0),units[cid])
     ledger.update(users.keys());weights.update({n:D-c for n,c in users.items()});raw+=netraw;pernet[net]=(set(users),{n:D-c for n,c in users.items()},netraw)
    assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items() if v};assert dict(independent)=={int(n):v for n,v in frame['independent_connection_ledger'].items() if v};return ledger,weights,raw,pernet
   oldledger,oldweights,oldraw,oldnets=interpret(old);newledger,newweights,newraw,newnets=interpret(new);assert all(newledger[n]<=max(oldledger[n],caps[n]) for n in oldledger.keys()|newledger.keys());assert sum(max(0,v-caps[n]) for n,v in newledger.items())==new['overflow_units']==old['overflow_units'];assert new['overflow_nodes']==sum(v>caps[n] for n,v in newledger.items());assert new['eligible_for_legal_route_commit']==(new['overflow_units']==0)
   def value(n,l,w):return w*(base[n]*(1+max(0,l-caps[n]))+wire*span.get(n,0))
   def full(ledger,weights,raw):return raw+sum(value(n,v,weights[n]) for n,v in ledger.items())
   before=full(oldledger,oldweights,oldraw);after=full(newledger,newweights,newraw);assert before==summary['baseline_objective_numerator'] and Fraction(after-before,D)==Fraction(summary['selected_objective_delta'])<=0
   proposals=json.loads((E/f'mmc_channel_diamond_Pareto_v1_2026-10-18/{case}_proposals.json').read_text());assert len(proposals)==8 and summary['selected']['mask']==255
   changed={cid for cid in bycid if newcid[cid]!=bycid[cid]};expected={c['connection_id'] for p in proposals for c in p['changes']};assert changed==expected and len(changed)==14
   chosenNETs={p['net_id'] for p in proposals}
   for key,epoch in old['epochs'].items():assert new['epochs'][key]==epoch+(int(key) in chosenNETs)
   assert old['epochs'].keys()==new['epochs'].keys()
   for key in old.keys()-{'records','ledger','independent_connection_ledger','epochs','overflow_units','overflow_nodes','eligible_for_legal_route_commit','status','scope'}:assert new[key]==old[key]
   for entry in matrix:
    dl=collections.Counter();dw=collections.Counter();dr=0
    for i,p in enumerate(proposals):
     if entry['mask']>>i&1:
      net=p['net_id'];a,aw,ar=oldnets[net];b,bw,br=newnets[net];dr+=br-ar
      for n in a|b:dl[n]+=int(n in b)-int(n in a);dw[n]+=bw.get(n,0)-aw.get(n,0)
    touched=dl.keys()|dw.keys();delta=dr+sum(value(n,oldledger[n]+dl[n],oldweights[n]+dw[n])-value(n,oldledger[n],oldweights[n]) for n in touched);capacity=all(0<=oldledger[n]+dl[n]<=max(oldledger[n],caps[n]) for n in touched);overflow=sum(max(0,oldledger[n]+dl[n]-caps[n])-max(0,oldledger[n]-caps[n]) for n in touched);assert entry['objective_delta_numerator']==delta and entry['capacity_nonincrease']==capacity and entry['overflow_delta']==overflow and entry['admitted']==(capacity and overflow<=0 and delta<=0)
   selected=min((v for v in matrix if v['admitted']),key=lambda v:(-v['NETs'],v['objective_delta_numerator'],v['mask']));assert selected==summary['selected'];bindings[str(newp)]=sha(newp);bindings[str(matrixp)]=sha(matrixp);results.append(dict(case=case,all_queries_checked_each_state=115572,NETs=len(nets),subsets_verified=256,changed_queries=14,full_objective_delta=str(Fraction(after-before,D)),overflow=new['overflow_units']));print('JOINT FULL FRAME AUDIT CASE PASS',case,flush=True)
  for p,h in bindings.items():assert sha(p)==h
  with (d/'independent_full_frame_v1.json').open('x') as f:json.dump(dict(status='all_three_joint_candidates_full_frame_Fraction_NET_ledger_objective_and256subsets_pass',bindings=bindings,rows=results,scope='Complete model-state admission only. Additive RC excludes route-tree loads/STA; Remaining source overflows are not a legal route. No native import, original full prediction gate, unseen-family or complete-time benefit inferred.'),f,indent=2)
 print('ALL THREE JOINT FULL FRAME AUDITS PASS',flush=True)
if __name__=='__main__':main()
