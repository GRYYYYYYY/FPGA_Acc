"""Initial setup boundaries, exact native windows and original RR rectangle geometry."""
import array,collections,json,struct,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from native_seed_phase_replay_v1 import replay,MAX
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';source=E/'mmc_native_connection_seed_phase_v1_2026-10-18';rp=source/'cohort_equivalence.json';r=json.loads(rp.read_text());assert len(r['rows'])==6 and r['all6_native_full_output_bytes_integer_counters_equal'];corep=E/'native_seed_phase_replay_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert len(core['corrupt_fixtures_rejected'])==13;cp=E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json';cert=json.loads(cp.read_text());qp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';assert sha(qp)==cert['bindings'][str(qp)];inv={}
 for line in qp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin=map(int,t[1:4]);inv[net,pin]=cid
 assert len(inv)==115572;out=E/'mmc_initial_frontier_replay_v1_2026-10-18';out.mkdir(exist_ok=False);graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';bindings={**r['bindings'],**{str(p):sha(p) for p in [rp,corep,cp,qp,Path(__file__),R/'tools/native_seed_phase_replay_v1.py',R/'tools/native_seed_context_replay_v1.py']}};rows=[]
 fields=['sequence','CID','initial_mode','initial_seed_pushes','initial_unique_seed_RRs','initial_min_same_layer_L1_or_MAX','source_sink_L1','total_heap_pushes','total_heap_pops','total_seed_pushes','phase_count','initial_same_layer_unique_seed_RRs']
 (out/'schema.json').write_text(json.dumps(dict(header='RC_INITIAL_FRONTIER_LE64 1',record_type='<12Q',record_fields=fields,mode={'0':'normal full-tree setup','1':'high-fanout spatial setup'},undefined_distance=MAX,scope='Initial phase only; tile rectangle L1 gap is not exact directed RR distance. Dynamic native execution context, not a certified RouteCast source-only consumer or full-flow speed benefit.'),indent=2))
 with Cache().installed():
  assert all(sha(p)==h for p,h in bindings.items());assert sha(graph)==bindings[str(graph)];coords=[array.array('I',[0])*904438 for _ in range(5)];seen=set();stack=[]
  for event,n in ET.iterparse(graph,events=['start','end']):
   if event=='start':stack.append(n);continue
   parent=stack[-2] if len(stack)>1 else None
   if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
    i=int(n.get('id'));assert i not in seen and i<904438;seen.add(i);loc=n.find('loc');values=[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']]+[int(loc.get('layer','0'))]
    for a,v in zip(coords,values):a[i]=v
    parent.remove(n);n.clear()
   if n.tag=='rr_nodes':break
   stack.pop()
  assert len(seen)==904438;xlo,xhi,ylo,yhi,layer=coords
  for row in r['rows']:
   case,arm=row['case'],row['arm'];assert row['legacy_seed_context_byte_equal'];folder=source/case/arm;attempts=[None];pending=None
   with (folder/'connection_trace.tsv').open() as f:
    assert next(f)=='CONNECTION_TRACE 2\n'
    for line in f:
     t=line.split()
     if t[0]=='A':
      a=list(map(int,t[1:]));assert pending is None and a[0]==len(attempts);pending=a
     elif t[0] in ('C','F'):
      v=list(map(int,t[1:]));assert pending is not None and v[:4]==pending[:4];seq,it,net,pin,src,sink,bpush,bpop=pending;attempts.append((inv[net,pin],src,sink,bpush,bpop,v[4],v[5]));pending=None
   assert pending is None and len(attempts)-1==row['connection_attempts'];sub=out/(case+'__'+arm);sub.mkdir();target=sub/'initial_frontier.bin';initial=None;counts=0;undefined=0;strictly_closer=0;not_closer=0;initial_seeds=allseeds=0;phase_hist=collections.Counter();cid_calls=array.array('Q',[0])*115572
   with target.open('xb') as output:
    output.write(b'RC_INITIAL_FRONTIER_LE64 1\n')
    def flush():
     nonlocal initial,counts,undefined,strictly_closer,not_closer,initial_seeds
     if initial is None:return
     seq=initial[0];cid,src,sink,bpush,bpop,apush,apop=attempts[seq];assert bpush<=initial[12]<=apush and bpop<=initial[13]<=apop
     assert xlo[src]==xhi[src] and ylo[src]==yhi[src] and xlo[sink]==xhi[sink] and ylo[sink]==yhi[sink] and layer[src]==layer[sink]
     source_l1=abs(xlo[src]-xlo[sink])+abs(ylo[src]-ylo[sink]);record=[seq,cid,initial[1],initial[2],initial[3],initial[4],source_l1,apush-bpush,apop-bpop,initial[5],initial[6],initial[7]];output.write(struct.pack('<12Q',*record));cid_calls[cid]+=1;counts+=1;undefined+=initial[4]==MAX;strictly_closer+=initial[4]!=MAX and initial[4]<source_l1;not_closer+=initial[4]!=MAX and initial[4]>=source_l1;initial_seeds+=initial[2];phase_hist[initial[6]]+=1
    def emit(v,nodes):
     nonlocal initial,allseeds
     seq=v['sequence'];cid,src,sink,bpush,bpop,apush,apop=attempts[seq];assert bpush<=v['begin_heap_pushes']<=v['end_heap_pushes']<=apush and bpop<=v['begin_heap_pops']==v['end_heap_pops']<=apop;assert v['target_RR'] in [None,sink]
     if initial is None or initial[0]!=seq:
      flush();assert v['phase']==1 and v['begin_heap_pushes']==bpush and v['begin_heap_pops']==bpop;same=[n for n in nodes if layer[n]==layer[sink]];minimum=min((max(0,xlo[n]-xhi[sink],xlo[sink]-xhi[n])+max(0,ylo[n]-yhi[sink],ylo[sink]-yhi[n]) for n in same),default=MAX);initial=[seq,v['mode'],v['seed_pushes'],len(nodes),minimum,0,0,len(same),0,0,0,0,0,0]
     initial[5]+=v['seed_pushes'];initial[6]+=1;initial[12]=v['end_heap_pushes'];initial[13]=v['end_heap_pops'];allseeds+=v['seed_pushes']
    result=replay(folder/'seed_phase.bin',folder/'seed_context.bin',emit);flush()
   assert counts==row['connection_attempts']==result['attempts'] and allseeds==result['seed_pushes']==row['phase_seed_push_records'] and result['phases']==row['seed_setup_phases'] and undefined+strictly_closer+not_closer==counts
   p=sub/'attempts.u64';p.write_bytes(cid_calls.tobytes());result.update(case=case,arm=arm,initial_seed_pushes=initial_seeds,later_phase_seed_pushes=allseeds-initial_seeds,initial_distance_undefined_attempts=undefined,initial_min_gap_strictly_less_than_SOURCE_gap_attempts=strictly_closer,initial_min_gap_not_less_than_SOURCE_gap_attempts=not_closer,phases_per_attempt_histogram=dict(phase_hist),frontier_file=dict(path=str(target),sha256=sha(target),records=counts),attempt_vector=dict(path=str(p),sha256=sha(p),values=115572,typecode='Q',byteorder=sys.byteorder));rows.append(result);print('INITIAL FRONTIER REPLAY PASS',case,arm,result['phases'],result['additional_phases'],strictly_closer,undefined,flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as f:json.dump(dict(status='all6_initial_phase_native_windows_legacy_projection_and_CID_frontiers_pass',bindings=bindings,rows=rows,scope='Initial phase geometry over actual seeded RR rectangles; later fallback phases separate. Not exact directional path length, offline source-only feature availability or complete-time/quality benefit. Independent raw phase/CID/geometry verification pending.'),f,indent=2)
if __name__=='__main__':main()
