"""Exhaustive joint source-cost admission of8whole-NET proposals; staged frames only."""
import sys,json,math,copy,collections,time
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_design_routing_inputs_v2 import load
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';source=E/'mmc_channel_diamond_Pareto_v1_2026-10-18';vp=source/'verification_v1.json';verification=json.loads(vp.read_text());assert len(verification['rows'])==24
 p=source/'protocol.json';plan=json.loads(p.read_text());costp=E/'mmc_objective_terminal_subset_v1_2026-10-18/protocol.json';cost=json.loads(costp.read_text());out=E/'mmc_joint_channel_diamond_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={**verification['bindings'],str(vp):sha(vp),str(p):sha(p),str(costp):sha(costp),**closure([Path(__file__)])};summaries=[]
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cost_inputs=cost['inputs'],subset_rule='Enumerate all256subsets of8verified proposals per case. Require each affected occupancy<=max(old,capacity), global overflow nonincrease and exact full weighted objective nonincrease. Prefer most accepted NETs, then least objective delta, then integer mask.',objective='sum_pin c*additive_RC + sum_resource sum_NET(1-max_user_c)*(base*(1+max(0,occ-capacity))+span/(20ns)); source history must be empty; use authenticated original base/criticalities for this endpoint.',scope='Source-only joint feasibility and cost admission; output frames are new staged model candidates, not native routing, new cold-label gates or independent-test certification.'),indent=2))
 with Cache().installed():
  for name,h in bindings.items():assert sha(name)==h
  print('JOINT CHANNEL GRAPH LOAD',flush=True);graph,digest,nodes,f,rc,_=load_endpoints(plan['inputs']['case_01']['endpoint']);dest_by_id={eid:f['dest_ranks'][s] for s,eid in enumerate(f['edge_ids'])};caps=f['capacities'];span={}
  for i,n in enumerate(nodes):
   if n.get('type') in ['CHANX','CHANY']:
    loc=n.find('loc');span[i]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  wire=rc.scale//(20*10**9)
  for case,data in plan['inputs'].items():
   tick=time.perf_counter();inputs=cost['inputs'][case];assert inputs['endpoint']==data['endpoint'];base,crit,extra=load(data['endpoint'],inputs['node_base_proof'],inputs['criticality_directory'],len(nodes),rc.scale);bindings.update(extra);frame=json.loads(Path(data['frame']).read_text());assert not frame['history'] and frame['scale']==rc.scale;D=math.lcm(*(x['criticality_denominator'] for x in crit.values()));units={cid:x['criticality_numerator']*(D//x['criticality_denominator']) for cid,x in crit.items()};nets=collections.defaultdict(list)
   for row in frame['records']:nets[row['net_id']].append(row)
   ledger=collections.Counter();weights=collections.Counter();independent=collections.Counter();raw=0
   for net,rows in nets.items():
    users={}
    for row in rows:
     c=units[row['connection_id']];owned={row['source']}|{dest_by_id[e] for e in row['answer']['physical_edge_ids']};independent.update(owned);raw+=c*row['answer']['delay']
     for n in owned:users[n]=max(users.get(n,0),c)
    ledger.update(users.keys());weights.update({n:D-c for n,c in users.items()})
   assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items() if v};assert dict(independent)=={int(n):v for n,v in frame['independent_connection_ledger'].items() if v};proposals_path=source/(case+'_proposals.json');proposals=json.loads(proposals_path.read_text());assert len(proposals)==8;bindings[str(proposals_path)]=sha(proposals_path);changes=[]
   for prop in proposals:
    changed=prop['changes'];w=D-max(units[r['connection_id']] for r in changed);rawdelta=sum(units[r['connection_id']]*(r['new_delay']-r['old_delay']) for r in changed);changes.append((prop['old_node'],prop['new_node'],w,rawdelta))
   touched={n for a,b,w,rawdelta in changes for n in [a,b]}
   def resource_value(n,l,w):return w*(base[n]*(1+max(0,l-caps[n]))+wire*span.get(n,0))
   before=raw+sum(resource_value(n,l,weights[n]) for n,l in ledger.items());matrix=[]
   for mask in range(256):
    ld=collections.Counter();wd=collections.Counter();rd=0
    for i,(a,b,w,rawdelta) in enumerate(changes):
     if mask>>i&1:ld[a]-=1;ld[b]+=1;wd[a]-=w;wd[b]+=w;rd+=rawdelta
    capacity=all(0<=ledger[n]+ld[n]<=max(ledger[n],caps[n]) for n in touched);overflow_delta=sum(max(0,ledger[n]+ld[n]-caps[n])-max(0,ledger[n]-caps[n]) for n in touched);delta=rd+sum(resource_value(n,ledger[n]+ld[n],weights[n]+wd[n])-resource_value(n,ledger[n],weights[n]) for n in touched);matrix.append(dict(mask=mask,NETs=mask.bit_count(),capacity_nonincrease=capacity,overflow_delta=overflow_delta,objective_delta_numerator=delta,admitted=capacity and overflow_delta<=0 and delta<=0))
   selected=min((v for v in matrix if v['admitted']),key=lambda v:(-v['NETs'],v['objective_delta_numerator'],v['mask']));mask=selected['mask'];candidate=copy.deepcopy(frame);records={r['connection_id']:r for r in candidate['records']};newledger=collections.Counter(ledger);newindependent=collections.Counter(independent);changed_cids=set()
   for i,prop in enumerate(proposals):
    if not mask>>i&1:continue
    a,b=prop['old_node'],prop['new_node'];newledger[a]-=1;newledger[b]+=1
    for change in prop['changes']:
     cid=change['connection_id'];assert cid not in changed_cids;changed_cids.add(cid);row=records[cid];assert row['answer']['physical_edge_ids']==change['old_edges'];row['answer']['physical_edge_ids']=change['new_edges'];row['answer']['delay']=change['new_delay'];newindependent[a]-=1;newindependent[b]+=1
    key=str(prop['net_id']);candidate['epochs'][key]=candidate['epochs'][key]+1
   candidate['ledger']={str(n):v for n,v in newledger.items() if v};candidate['independent_connection_ledger']={str(n):v for n,v in newindependent.items() if v};candidate['overflow_units']=sum(max(0,v-caps[n]) for n,v in newledger.items());candidate['overflow_nodes']=sum(v>caps[n] for n,v in newledger.items());candidate['eligible_for_legal_route_commit']=candidate['overflow_units']==0;candidate['status']='JOINT_CHANNEL_DIAMOND_STAGED';candidate['scope']='Joint source-cost admitted model candidate; no native or forecast-quality admission.'
   artifact=out/case;artifact.mkdir();(artifact/'candidate.json').write_text(json.dumps(candidate,separators=(',',':')));(artifact/'subset_matrix.json').write_text(json.dumps(matrix,separators=(',',':')));summary=dict(case=case,subsets=256,admitted_subsets=sum(x['admitted'] for x in matrix),selected=selected,objective_denominator=D,baseline_objective_numerator=before,selected_objective_delta=str(Fraction(selected['objective_delta_numerator'],D)),changed_queries=len(changed_cids),old_overflow=frame['overflow_units'],new_overflow=candidate['overflow_units'],component_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in artifact.iterdir()});summaries.append(summary);print('JOINT CHANNEL CASE DONE',json.dumps(summary),flush=True)
  for name,h in bindings.items():assert sha(name)==h
  with (out/'receipt.json').open('x') as f:json.dump(dict(status='all_three_joint_channel_candidates_staged_independent_full_frame_audit_pending',bindings=bindings,summaries=summaries,scope='New isolated model frames, original source frames immutable. Full path/wholeNET/ledger/objective and native/cold utility checks remain distinct.'),f,indent=2)
if __name__=='__main__':main()
