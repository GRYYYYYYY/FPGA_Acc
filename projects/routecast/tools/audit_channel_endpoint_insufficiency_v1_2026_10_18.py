"""Existing same-endpoint source states distinguish channel ownership features."""
import hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/channel_endpoint_insufficiency_v1_2026-10-18');out.mkdir(exist_ok=False)
 root=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');gp=root/'groups.json';g=json.loads(gp.read_text());config=json.loads((root/'protocol.json').read_text())
 vp=Path('experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json');proof=json.loads(vp.read_text());assert proof['status']=='pass'
 bindings={str(p.resolve()):sha(p) for p in [gp,root/'protocol.json',vp,Path(__file__)]}
 channels={str(i) for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel'};ipins={str(i) for i,v in enumerate(g['groups']) if v['kind']=='direct_sink_IPIN'}
 methods=[m for m in config['methods'] if m!='previous_native'];results=[]
 for case,inputs in sorted(config['inputs'].items()):
  endpoint=Path(inputs['endpoint']);bindings[str(endpoint.resolve())]=sha(endpoint)
  journals={}
  for method in methods:
   path=root/(case+'__'+method+'.json');actual=sha(path);assert actual==proof['bindings'][str(path.resolve())]
   bindings[str(path.resolve())]=actual;d=json.loads(path.read_text());frame=Path(inputs['predictions'][method]);assert d['source_frame_sha256']==sha(frame)
   bindings[str(frame.resolve())]=d['source_frame_sha256'];journals[method]=d['positive_group_histograms']
  # All current source states were independently checked against one endpoint file.
  ep_proof=Path('experiments/mmc_IPIN_endpoint_sufficiency_v1_2026-10-18/verification.json');ep=json.loads(ep_proof.read_text());assert ep['status']=='pass' and ep['bindings'][str(endpoint.resolve())]==sha(endpoint);bindings[str(ep_proof.resolve())]=sha(ep_proof)
  baseline='native_retained_on';a=journals[baseline]
  for method in methods:
   b=journals[method];changed=[gid for gid in channels if a.get(gid)!=b.get(gid)]
   assert all(a.get(gid)==b.get(gid) for gid in ipins)
   results.append(dict(case=case,reference=baseline,source=method,same_endpoint_sha256=sha(endpoint),changed_channel_groups=len(changed),changed_IPIN_groups=0,multi_resource_NET_channel_groups=sum(any(int(k)>1 for k in row['NET_occupancy_histogram']) for gid,row in b.items() if gid in channels)))
 assert any(row['changed_channel_groups']>0 for row in results)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=results,conclusion='For the implemented source-conditioned channel prior, endpoints alone are insufficient: identical endpoints have different verified channel NET/group ownership histograms. This does not prove impossibility of a different endpoint-only statistical predictor.',required_delta='To reproduce current typed channel scores, maintain per-NET unique node/group ownership from path changes with shared-query reference counts, update group k histograms when last/first NET-node references change, and publish channel score state with the same endpoint/path generation.',scope='Existing exposed source states, no new forecast labels or native execution; no forecast gate promotion.'),f,indent=2)
 print(json.dumps(results))
if __name__=='__main__':main()
