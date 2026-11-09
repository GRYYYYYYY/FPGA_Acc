"""Authenticate fresh wire-span full cohort; native full scope and fixed cold quality gates."""
import sys,json,re
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
out=R/'experiments/aes_affected_cache_full_workflow_v1_2026-10-08';rp=out/'receipt.json';data=json.loads(rp.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={**closure([Path(__file__)]),str(rp):sha(rp)};rows=[]
for row in data['rows']:
 name=row['name'];assert row['status']=='COMPLETE_WORKFLOW_CANONICAL_PASS';w=out/name;assert all(sha(k)==v for k,v in row['files'].items());assert all(sha(k)==v for k,v in row['canonical']['files'].items())
 ref=R/'experiments/aes_native_demand_estimates_v1_2026-10-08'/name
 all_ep=json.loads((w/'all_endpoints.json').read_text());assert all_ep['connections']==json.loads((R/'experiments/aes_rr_graph_only_v1_2026-10-08'/name/'endpoints.json').read_text())['connections']
 ep=json.loads((w/'endpoints.json').read_text());reference=json.loads((R/'experiments/aes_native_demand_frontend_v1_2026-10-08'/name/'endpoints.json').read_text());assert ep['connections']==reference['connections'] and ep['graph_sha256']==reference['graph_sha256'];partition=json.loads((w/'scope_partition.json').read_text());ident={x['name']:x for x in map(json.loads,(w/'identity.jsonl').read_text().splitlines())};physical=[];ignored=[]
 for q in all_ep['connections']:
  n=all_ep['net_names'][str(q['net_id'])];assert n in ident
  if ident[n]['ignored']:ignored.append(q)
  else:physical.append(q)
 assert len(physical)+len(ignored)==row['all_original_queries'] and len(ignored)==row['native_ignored_queries'];assert [x['query'] for x in partition['ignored']]==ignored
 assert partition['translation']==[{'physical_connection_id':i,'original_connection_id':q['connection_id']} for i,q in enumerate(physical)];assert ep['connections']==[{**q,'connection_id':i} for i,q in enumerate(physical)]
 assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());assert sha(w/'identity.jsonl')==ep['inputs']['native_identity']['sha256']
 for f in ['resident/floors.json','resident/initial.json','resident/sketch.json']:
  assert json.loads((w/f).read_text())==json.loads((ref/f).read_text());bindings[str(ref/f)]=sha(ref/f)
 for i in range(2):
  a=json.loads((w/f'resident/round{i}.json').read_text());b=json.loads((ref/f'resident/round{i}.json').read_text());assert a==b
 ep=json.loads((w/'endpoints.json').read_text());a=audit(Path(ep['inputs']['graph']['path']),w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert actual==required and a['overflow_units']==0
 for file in [w/'native.log',out/(name+'_canonical')/'reload.log']:
  text=file.read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==row['cpd_ns']
 assert row['canonical']['semantic_consistency_gate_pass'] and row['canonical']['packed_netlist_byte_identical'] and row['canonical']['all_NET_physical_node_type_switch_sequences_identical'];assert row['canonical']['original_zero_counter_gate_pass'] is False
 assert row['canonical']['mismatches']==row['canonical']['fixups']==row['native_ignored_queries']
 required_stages={'conversion','native_demand_partition','resident','selection','identity_serialization','native','audit','canonical'};assert set(row['stages'])==required_stages and sum(row['stages'].values())<=row['actual_complete_workflow_seconds'] and all(v>=0 for v in row['stages'].values())
 rows.append(dict(name=name,connections=len(ep['connections']),seed_cpd_ns=row['cpd_ns'],seed_wirelength=row['wirelength'],actual_full_seconds=row['actual_complete_workflow_seconds']))
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'fresh_estimates_native_full_endpoints_capacity_canonical_pass':True,'fresh_paired_cold_done':False,'originalHDL_semantic_relation_proven':False,'mapped_candidate_scope_only':True,'previously_observed_family':True,'original_zero_counter_gate_pass':False},indent=2)+'\n');print(json.dumps(rows,indent=2))
