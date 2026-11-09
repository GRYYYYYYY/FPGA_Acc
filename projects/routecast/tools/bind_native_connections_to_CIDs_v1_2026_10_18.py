"""Three-way frozen ordinal/physical pin/current RR binding; complete CID labels."""
import sys,json,array,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,placements
from versioned_digest_cache_v1 import Cache

def main():
 E=R/'experiments';replaydir=E/'mmc_native_connection_replay_v1_2026-10-18';rp=replaydir/'verification.json';replayed=json.loads(rp.read_text());assert len(replayed['rows'])==6;ordinalp=E/'native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';ordinalproofp=E/'mmc_native_iteration_state_observer_v2_2026-10-10/pin_identity_audit_v1.json';ordinalproof=json.loads(ordinalproofp.read_text());assert ordinalproof['all21rounds_all115572_manifest_NET_local_pin_source_sink_identity_pass'];assert sha(ordinalp)==ordinalproof['bindings'][str(ordinalp)];frozen={}
 for line in ordinalp.read_text().splitlines():
  t=line.split()
  if t[0]=='Q':cid,net,pin,src,sink=map(int,t[1:]);assert cid not in frozen;frozen[cid]=(net,pin)
 assert len(frozen)==115572 and len(set(frozen.values()))==115572;specp=E/'mmc_native_owner_cascade_trace_spec_v1_2026-10-18.json';spec=json.loads(specp.read_text());out=E/'mmc_native_connection_CID_binding_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py',rp,ordinalp,ordinalproofp,specp]};results=[]
 with Cache().installed():
  for case in ['case_01','case_02','case_03']:
   base=E/'mmc_multiplacement_inputs_v1_2026-10-18'/case;epfile=base/'demand/endpoints.json';ep=json.loads(epfile.read_text());dp=base/'demand/verification.json';demandproof=json.loads(dp.read_text());assert demandproof['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'];assert sha(epfile)==demandproof['bindings'][str(epfile)];partp=base/'demand/scope_partition.json';part=json.loads(partp.read_text());rawp=Path(ep['inputs']['all_endpoints']['path']);raw=json.loads(rawp.read_text());netp=Path(ep['inputs']['net']['path']);placep=Path(ep['inputs']['place']['path']);mapp=netp.parent/'mapping.json';mproofp=netp.parent/'verification.json';mproof=json.loads(mproofp.read_text());assert mproof['complete_manifest_query_partition_and_original_XML_node_type_class_capacity_bbox_pass'];assert sha(mapp)==mproof['bindings'][str(mapp)];mapping=json.loads(mapp.read_text());identityp=Path(ep['inputs']['native_identity']['path']);identities=[json.loads(x) for x in identityp.read_text().splitlines()];pos=placements(placep,sha(netp));assert sha(netp)==ordinalproof['bindings'][str(E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/design.net')]
   for desc in ep['inputs'].values():assert sha(desc['path'])==desc['sha256']
   for p in [epfile,dp,partp,rawp,netp,placep,mapp,mproofp,identityp]:bindings[str(p)]=sha(p)
   physical={};sinks=collections.defaultdict(list);drivers={}
   for pin in mapping['pin_details']:
    key=(pin['net'],pin['block'],pin['port'],pin['bit']);assert key not in physical;physical[key]=pin
    if pin['role']=='SINK':sinks[pin['net_id']].append(pin)
    else:assert pin['role']=='SOURCE' and pin['net_id'] not in drivers;drivers[pin['net_id']]=pin
   native_by_key={};native_meta={};expected_rr={}
   for native in identities:
    net=native['net_id'];assert net not in native_meta;native_meta[net]=dict(name=native['name'],ignored=native['ignored'],pins=len(native['pins']))
    for pin in native['pins']:
     key=(native['name'],pin['block'],pin['port'],pin['bit']);assert key in physical and key not in native_by_key;actual=physical[key];assert actual['physical_pin_ptc']==pin['physical_pin'] and actual['class_id']==pin['class'];x,y,z,layer,_=pos[pin['block']];assert (x,y,layer)==(pin['x'],pin['y'],pin['layer']);assert actual['role']==('SOURCE' if pin['index']==0 else 'SINK');native_key=(net,pin['index']);native_by_key[key]=native_key;assert native_key not in expected_rr;expected_rr[native_key]=actual['rr_node']
   assert set(native_by_key)==set(physical);offset=collections.Counter();raw_to_native={}
   for q in raw['connections']:
    net=q['net_id'];name=raw['net_names'][str(net)];pin=sinks[net][offset[net]];offset[net]+=1;assert pin['net']==name and pin['rr_node']==q['sink'] and drivers[net]['rr_node']==q['source'];raw_to_native[q['connection_id']]=native_by_key[name,pin['block'],pin['port'],pin['bit']]
   translations=part['physical_to_original_connection_ids'];assert len(translations)==len(ep['connections'])==115572;binding=[]
   for entry,q in zip(translations,ep['connections']):
    cid=entry['physical_connection_id'];original=entry['original_connection_id'];assert cid==q['connection_id'] and dict(raw['connections'][original],connection_id=cid)==q;key=raw_to_native[original];assert key==frozen[cid];assert native_meta[key[0]]['name']==ep['net_names'][str(q['net_id'])] and not native_meta[key[0]]['ignored'];assert expected_rr[key]==q['sink'] and expected_rr[key[0],0]==q['source'];binding.append(dict(connection_id=cid,manifest_NET=q['net_id'],native_NET=key[0],native_sink_index=key[1],source=q['source'],sink=q['sink']))
   assert len({(b['native_NET'],b['native_sink_index']) for b in binding})==115572;caseout=out/case;caseout.mkdir();bp=caseout/'CID_native_binding.jsonl'
   with bp.open('x') as f:
    for b in binding:f.write(json.dumps(b,separators=(',',':'))+'\n')
   for arm in ['off','on']:
    recorded=next(v for v in replayed['rows'] if v['case']==case and v['arm']==arm);src=replaydir/(case+'__'+arm);np=src/'native_NETs.json';cp=src/'native_sink_counts.jsonl';assert sha(np)==recorded['files'][str(np)] and sha(cp)==recorded['files'][str(cp)];meta={int(k):v for k,v in json.loads(np.read_text()).items()};assert meta==native_meta;counts={}
    for line in cp.read_text().splitlines():
     v=json.loads(line);key=(v['native_NET'],v['native_sink_index']);assert key not in counts and expected_rr[key]==v['sink_RR'] and expected_rr[key[0],0]==v['source_RR'];assert v['native_ignored']==meta[key[0]]['ignored'];counts[key]=v
    wanted={(b['native_NET'],b['native_sink_index']) for b in binding};assert wanted=={key for key,v in counts.items() if not v['native_ignored']};extras=set(counts)-wanted;assert all(counts[k]['native_ignored'] for k in extras)
    job=next(j for j in spec['jobs'] if j['case']==case and bool(j['preserve_partial_first_iteration'])==(arm=='on'));seedp=Path(job['seed']);assert sha(seedp)==replayed['bindings'][str(seedp)];seedpins={};current=None
    for line in seedp.read_text().splitlines():
     t=line.split()
     if t and t[0]=='Net':current=int(t[1]);assert line.strip().startswith('Net '+str(current)+' ('+meta[current]['name']+')')
     elif t and t[0]=='Node:' and 'SINK' in t and 'Net_pin_index:' in t:
      pin=int(t[t.index('Net_pin_index:')+1])
      if pin>0:key=(current,pin);assert key not in seedpins;seedpins[key]=int(t[1])
    reached={key:v['sink_RR'] for key,v in counts.items() if v['initially_reached']};assert seedpins==reached
    success=array.array('Q');failed=array.array('Q');initial=array.array('B');rerouted=array.array('B')
    for b in binding:
     v=counts[b['native_NET'],b['native_sink_index']];success.append(v['successful_sink_operations']);failed.append(v['failed_sink_attempts']);initial.append(int(v['initially_reached']));rerouted.append(int(v['observed_explicit_reroute']))
    assert sum(success)==recorded['successful'];target=caseout/arm;target.mkdir();vectors={}
    for name,data in [('successful_sink_operations',success),('failed_sink_attempts',failed),('initial_seed_reached',initial),('observed_explicit_reroute',rerouted)]:
     p=target/(name+('.u64' if data.itemsize==8 else '.u8'));p.write_bytes(data.tobytes());vectors[name]=dict(path=str(p),sha256=sha(p),values=len(data),itemsize=data.itemsize,typecode=data.typecode,byteorder=sys.byteorder)
    bindings[str(np)]=sha(np);bindings[str(cp)]=sha(cp);bindings[str(seedp)]=sha(seedp);summary=dict(case=case,arm=arm,manifest_CIDs=115572,complete_current_physical_pins_verified=len(physical),native_ignored_sink_pins_excluded=len(extras),initial_seed_CIDs=sum(initial),successful_sink_operations=sum(success),distinct_routed_CIDs=sum(x>0 for x in success),distinct_explicit_rerouted_CIDs=sum(rerouted),zero_success_CIDs=sum(x==0 for x in success),seed_and_initial_native_flags_exact=True,binding_file=str(bp),binding_sha256=sha(bp),vectors=vectors);results.append(summary);print('CID BINDING PASS',case,arm,summary['distinct_routed_CIDs'],summary['distinct_explicit_rerouted_CIDs'],flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as f:json.dump(dict(status='all6_complete_manifest_CID_native_pin_physical_RR_and_seed_bindings_pass',bindings=bindings,rows=results,scope='Frozen native ordinal map and independent current native physical-pin join agree on all115572CIDs; current trace NET metadata, source/SINK RR classes and seed printed pin indices matched exactly. RRR label is explicit successful native sink re-invocation relative to initial imported seed or earlier success. Shared-trunk side effects on other CIDs, per-CID heap/time, policy causal benefit, independent families and original-zero-counter gate are not certified.'),f,indent=2)
 print('ALL6MANIFEST CID BINDINGS PASS',flush=True)
if __name__=='__main__':main()
