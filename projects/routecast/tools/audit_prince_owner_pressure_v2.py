"""Same-process ownership, pre-release semantics and independent binary32 algebra."""
import json,struct,re,subprocess,time
from pathlib import Path
from collections import Counter,defaultdict
from dataclasses import FrozenInstanceError
from pre_route_endpoints import sha
from audit_native_route import NODE
from owner_conditioned_pressure_v2 import Snapshot,PHASE,word
from prince_configuration_identity_v1 import profile
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_owner_pressure_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);start=time.perf_counter();pp=E/'prince_owner_pressure_design_v2_2026-10-20/protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());root=E/'prince_resident_phase_trial_v1_2026-10-20';vp=root/'phase_verification_v1.json';source=json.loads(vp.read_text());jp=E/'prince_resident_phase_trial_design_v1_2026-10-20/protocol.json';jobs={j['case']:j for j in json.loads(jp.read_text())['jobs']};readyfile=E/'prince_ready_consumer_trial_v1_2026-10-20/ready_event_verification_v1.json';ready={x['case']:x['selected_iteration'] for x in json.loads(readyfile.read_text())['rows'] if x['mode']=='digest'};bindings={str(q):sha(q) for q in [pp,vp,jp,readyfile,Path(__file__),R/'tools/owner_conditioned_pressure_v2.py']};rows=[];query_count=0;pressure_different=0;eligible_pairs=0
 pattern=re.compile(r'^Net (\d+) \((.*)\)(: global net connecting:)?\s*$')
 with (D/'scalar_queries.txt').open('x') as queries,(D/'expected_scalar_words.jsonl').open('x') as expected:
  for caseproof in source['rows']:
   case=caseproof['case'];capture=root/case/'capture';mappingp=E/'prince_resident_consumer_v1_2026-10-20'/case/'NET_mapping.json';mapping={x['native_NET_id']:x for x in json.loads(mappingp.read_text())};data={n for n,x in mapping.items() if not x['ignored_global']};resourcep=E/'prince_quality_domains_v1_2026-10-20'/case.split('/')[0]/'resources.jsonl';caps={x['id']:x['capacity'] for x in map(json.loads,resourcep.open())};phase=[list(map(int,line.split())) for line in (capture/'boundary/phase.tsv').read_text().splitlines()];job=jobs[case+'/capture'];ep=E/'prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';endpoint=json.loads(ep.read_text());_,launch=profile(job['command'],Path(job['staging']['design.blif']));binary=Path(job['command'][0]);binarysha=sha(binary);roles={1:['first_iteration'],2:['second_iteration'],len(phase):['terminal_including_failed']}
   if ready[case] is not None:roles.setdefault(ready[case],[]).append('fixed_ready_event')
   for iteration,role in sorted(roles.items()):
    trace=capture/f'iteration_{iteration:03d}.route';owners={net:set() for net in data};headers={};current=None
    for line in trace.read_text().splitlines():
     match=pattern.fullmatch(line)
     if match:
      net,name=int(match[1]),match[2];assert net not in headers and mapping[net]['name']==name and bool(match[3])==mapping[net]['ignored_global'];headers[net]=name;current=net
     node=NODE.match(line)
     if node and node[2] in ['CHANX','CHANY']:nid=int(node[1]);assert current in data and nid in caps;owners[current].add(nid)
    assert set(headers)==set(mapping);rawp=capture/'boundary'/f'iteration_{iteration}.bin';raw=rawp.read_bytes();i,n=struct.unpack_from('<QQ',raw,8);assert i==iteration and len(raw)==24+24*n;native={nid:count for nid,kind,count,capacity,bits in struct.iter_unpack('<QIiiI',raw[24:]) if nid in caps};pres=phase[iteration-1][1];identity=(case,iteration,endpoint['graph_sha256'],endpoint['inputs']['net']['sha256'],endpoint['inputs']['place']['sha256'],binarysha,launch,PHASE);snapshot=Snapshot(identity,caps,native,owners,pres);views={net:snapshot.view(net,identity) for net in data};reverse=defaultdict(set)
    for net,nodes in owners.items():
     for node in nodes:reverse[node].add(net)
    count=Counter(node for nodes in owners.values() for node in nodes);assert all(count[node]==native[node] for node in caps);localpairs=localdifferent=0;ordered=sorted(data)
    for node,users in reverse.items():
     owner=min(users);outsider=next(net for net in ordered if net not in users);a=views[owner].multiplier_bits(node);b=views[outsider].multiplier_bits(node);fa=struct.unpack('<f',struct.pack('<I',a))[0];fb=struct.unpack('<f',struct.pack('<I',b))[0];assert fa<=fb
     for net,owned,bits in [(owner,1,a),(outsider,0,b)]:
      assert bits==views[net].multiplier_bits(node);queries.write(f'{query_count} {native[node]} {caps[node]} {owned} {pres}\n');expected.write(json.dumps(dict(query=query_count,bits=bits),separators=(',',':'))+'\n');query_count+=1
     localpairs+=1;localdifferent+=a!=b
    eligible_pairs+=localpairs;pressure_different+=localdifferent;out=D/case/f'iteration_{iteration:03d}';out.mkdir(parents=True);ownerp=out/'CHANNEL_owners.json';ownerp.write_text(json.dumps({str(net):sorted(nodes) for net,nodes in owners.items()},separators=(',',':'))+'\n');rows.append(dict(case=case,iteration=iteration,roles=role,data_NETs=len(data),CHANNEL_resources=len(caps),CHANNEL_owner_incidences=sum(len(nodes) for nodes in owners.values()),occupied_CHANNELs=localpairs,owner_outsider_pressure_distinct_nodes=localdifferent,pres_bits=pres,owner_payload=str(ownerp),owner_sha256=sha(ownerp)));print('OWNER_PRESSURE',case,iteration,localpairs,localdifferent,flush=True)
    for f in [trace,rawp,ownerp]:bindings[str(f)]=sha(f)
   for f in [mappingp,resourcep,capture/'boundary/phase.tsv',ep,binary]:bindings[str(f)]=sha(f)
 assert len(rows)==33
 # Identical local occupancy, different owner assignment: global scalar aliases.
 identity=('fixture',PHASE);A=Snapshot(identity,{0:1},{0:1},{0:{0},1:set()},word(.5));B=Snapshot(identity,{0:1},{0:1},{0:set(),1:{0}},word(.5));assert A.view(0,identity).multiplier_bits(0)==word(1.) and B.view(0,identity).multiplier_bits(0)==word(1.5);negative=0
 tests=[lambda:Snapshot(identity,{0:1},{0:1},{0:{0},1:set()},word(.5),release_stage='already_applied'),lambda:Snapshot(identity,{0:1},{0:0},{0:{0},1:set()},word(.5)),lambda:A.view(99,identity),lambda:A.view(0,('wrong',PHASE)),lambda:A.view(0,identity).multiplier_bits(99)]
 for fn in tests:
  try:fn()
  except ValueError:negative+=1
  else:raise AssertionError('invalid pressure input admitted')
 try:A.pres=0
 except FrozenInstanceError:negative+=1
 else:raise AssertionError('mutable snapshot')
 cpp=R/'tools/check_owner_pressure_scalar_v1.cpp';binary=D/'scalar_reference';compile=['/usr/bin/c++','-std=c++17','-O3',str(cpp),'-o',str(binary)]
 with (D/'build.log').open('x') as f:assert subprocess.call(compile,stdout=f,stderr=subprocess.STDOUT)==0
 with (D/'scalar_queries.txt').open() as inp,(D/'native_expression_words.txt').open('x') as out:assert subprocess.call([str(binary)],stdin=inp,stdout=out)==0
 checked=0
 with (D/'native_expression_words.txt').open() as actual:
  for line in (D/'expected_scalar_words.jsonl').open():
   expected=json.loads(line);qid,bits=map(int,next(actual).split());assert qid==expected['query']==checked and bits==expected['bits'];checked+=1
  assert actual.read()==''
 assert checked==query_count and negative==6
 for f in [cpp,binary,D/'scalar_queries.txt',D/'expected_scalar_words.jsonl',D/'native_expression_words.txt']:bindings[str(f)]=sha(f)
 assert all(sha(f)==h for f,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,snapshots=33,owner_outsider_node_pairs=eligible_pairs,distinct_pressure_pairs=pressure_different,exact_binary32_scalar_queries=checked,negative_contract_checks=negative,global_occupancy_alias_witness=True,bindings=bindings,component_seconds=time.perf_counter()-start,scope='Offline whole-NET virtual-release present-pressure algebra only, actual9-case/33-snapshot CHANNEL owner unions match same-process native RR counts. C++ reference uses pinned native scalar expression after virtual release, not the native connection router. Query outsiders need not have a feasible route through each queried node. First p0 phase may have equal prices. No mutable native release/preload, route legality, forecast quality, per-connection retained-branch equivalence or fullpaid/unseen gain. Snapshot provenance binds source binary/launcher; this archive predates independent resolved-option export.'),indent=2)+'\n');print('OWNER_PRESSURE_CONTRACT_PASS',len(rows),eligible_pairs,pressure_different,checked,negative)
if __name__=='__main__':main()
