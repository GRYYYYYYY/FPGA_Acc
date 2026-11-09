"""Independent full-path Fraction and whole-NET footprint verification of proposals."""
import sys,json,collections
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';d=E/'mmc_channel_diamond_support_v1_2026-10-18';rp=d/'receipt.json';r=json.loads(rp.read_text());protocol=json.loads((d/'protocol.json').read_text());bindings={**r['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};rows=[]
 with Cache().installed():
  for p,h in bindings.items():assert sha(p)==h
  _,digest,nodes,f,rc,_=load_endpoints(protocol['inputs']['case_01']['endpoint']);g=json.loads((E/'mmc_typed_collision_risk_v1_2026-10-18/groups.json').read_text());group_of={n:i for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel' for n in v['members']}
  for summary in r['summaries']:
   case=summary['case'];p=Path(summary['proposals_file']);assert sha(p)==summary['sha256'];bindings[str(p)]=sha(p);proposals=json.loads(p.read_text());frame=json.loads(Path(protocol['inputs'][case]['frame']).read_text());nets=collections.defaultdict(list)
   for record in frame['records']:nets[record['net_id']].append(record)
   for proposal in proposals:
    original=nets[proposal['net_id']];changes={v['connection_id']:v for v in proposal['changes']};assert len(changes)==len(proposal['changes']);footprints=[]
    for mode in ['old','new']:
     owned=set();parents={}
     for record in original:
      cid=record['connection_id'];path=record['answer']['physical_edge_ids']
      if cid in changes:
       change=changes[cid];assert change['old_edges']==path and change['old_delay']==record['answer']['delay'] and change['budget']==record['budget_integer']
       if mode=='new':path=change['new_edges']
      delay=rc.rc.path(record['source'],record['sink'],path);assert delay*rc.scale==(changes[cid]['new_delay'] if mode=='new' and cid in changes else record['answer']['delay']);assert delay<=Fraction(record['budget_integer'],rc.scale);node=record['source'];owned.add(node)
      for edge in path:
       matches=[s for s in range(f['row_offsets'][node],f['row_offsets'][node+1]) if f['edge_ids'][s]==edge];assert len(matches)==1;s=matches[0];v=f['dest_ranks'][s];assert f['capacities'][v]>0 and (v not in parents or parents[v]==(node,edge));parents[v]=(node,edge);owned.add(v);node=v
     footprints.append(owned)
    old,new=footprints;removed=old-new;added=new-old;assert removed=={proposal['old_node']} and added=={proposal['new_node']};assert group_of[proposal['old_node']]==proposal['old_group']!=proposal['new_group']==group_of[proposal['new_node']]
    ledger={int(n):v for n,v in frame['ledger'].items()};a,b=proposal['old_node'],proposal['new_node'];cap=f['capacities'];delta=max(0,ledger.get(a,0)-1-cap[a])-max(0,ledger.get(a,0)-cap[a])+max(0,ledger.get(b,0)+1-cap[b])-max(0,ledger.get(b,0)-cap[b]);rows.append(dict(case=case,NET=proposal['net_id'],changed_queries=len(changes),one_NET_channel_mass_delta=0,removed_channel=a,added_channel=b,isolated_global_overflow_delta=delta))
  for p,h in bindings.items():assert sha(p)==h
 out=d/'verification_v1.json';result=dict(status='all8_channel_diamond_proposals_full_NET_and_Fraction_verified',bindings=bindings,rows=rows,scope='All unchanged siblings and changed paths rechecked; exact one-channel removal/addition across groups, original endpoints/budgets and single-parent NET preserved. Overflow delta is isolated proposal only, not concurrent composition, full objective approval, native acceptance/STA, forecast or timing benefit. Original models unchanged.')
 assert len(rows)==8
 with out.open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(rows,indent=2),flush=True)
if __name__=='__main__':main()
