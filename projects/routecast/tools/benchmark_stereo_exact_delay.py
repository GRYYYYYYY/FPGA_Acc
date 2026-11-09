"""Paired ABBA query benchmark; shared preparation and class setup separate."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from prepared_csr import read,TYPES
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_min_delay_feasibility import query as fractional
from csr_integer_exact_delay import IntegerRC,query as integer_query

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'exact_delay_integer_abba';out.mkdir();(out/'source').mkdir();start=time.monotonic()
 root=b/'conflict_minimum_bypass_delay';candidate_root=b/'conflict_minimum_bypass_integer';files=[root/'results.json',root/'receipt.json',candidate_root/'candidates.json',candidate_root/'receipt.json',b/'exact_buffered_rc_classes_v2/receipt.json',b/'streaming_csr_class_cache_v3/csr/manifest.json']
 inputs={str(p):sha(p) for p in files};names=['benchmark_stereo_exact_delay.py','csr_integer_exact_delay.py','csr_min_delay_feasibility.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 reference=json.loads(files[0].read_text());assert json.loads(files[1].read_text())['results_sha256']==inputs[str(files[0])]
 candidates={x['connection_id']:x for x in json.loads(files[2].read_text())};requests=json.loads((b/'additional_high_fanout_physical_audit/conflict_repair_requests.json').read_text());req={x['connection_id']:x for x in requests['requests']}
 reqpath=b/'additional_high_fanout_physical_audit/conflict_repair_requests.json';inputs[str(reqpath)]=sha(reqpath)
 graph=json.loads((b/'exact_buffered_rc_classes_v2/protocol.json').read_text())['graph']['sha256']
 protocol={'inputs':inputs,'sources':sources,'graph_sha256':graph,'sequence':['fractional','integer','integer','fractional']*2,'queries_per_run':5,'scope':'same-host paired full five-query implementation comparison; no hardware, feedback/net-routing cost or QoR claim; common CSR preparation and exact class setup separately measured'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');_,f=read(b/'streaming_csr_class_cache_v3/csr',graph);ids,classes,switches=load(b/'exact_buffered_rc_classes_v2',graph);rc=ExactBufferedRC(f,ids,classes,switches);common_s=time.monotonic()-start;cs=time.monotonic();ctx=IntegerRC(rc);class_setup_s=time.monotonic()-cs
 upper=max(ctx.starts)+(len(ids)-1)*max(ctx.weights.values());upper=Fraction(upper,ctx.scale);runs=[]
 for implementation in protocol['sequence']:
  qs=time.monotonic();outputs=[]
  for expected in reference:
   cid=expected['connection_id'];row=req[cid];c=candidates[cid];opins=set(c['source_opins']);ipins=set(c['target_ipins']);blocked=set(row['conflict_rr_nodes']);source=row['source'];sink=row['sink']
   def allowed(n,i):
    d=f['dest_ranks'][i]
    if d in blocked or f['capacities'][d]<=0:return False
    if n==source:return d in opins
    if n in ipins:return d==sink
    return (n in opins or f['types'][n] in (TYPES['CHANX'],TYPES['CHANY'])) and (d in ipins or f['types'][d] in (TYPES['CHANX'],TYPES['CHANY']))
   result=fractional(rc,source,sink,upper,allowed,max_labels=len(ids)) if implementation=='fractional' else integer_query(ctx,source,sink,upper,allowed,max_nodes=len(ids))
   for key in ('status','physical_edge_ids','settled_nodes','discovered_nodes','examined_edges'):assert result[key]==expected[key]
   assert result['delay']==Fraction(*expected['delay']);outputs.append(cid)
  record={'implementation':implementation,'wall_s':time.monotonic()-qs,'verified_connections':outputs};runs.append(record);(out/'runs.json').write_text(json.dumps(runs,indent=2)+'\n');print(json.dumps(record),flush=True)
 assert all(sha(k)==h for k,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
 pairs=[{'fractional_s':runs[a]['wall_s'],'integer_s':runs[c]['wall_s'],'query_ratio':runs[a]['wall_s']/runs[c]['wall_s']} for a,c in [(0,1),(3,2),(4,5),(7,6)]]
 receipt={'runs':8,'paired_queries':40,'pairs':pairs,'common_load_and_authenticate_s':common_s,'integer_class_setup_s':class_setup_s,'integer_scale_bits':ctx.scale.bit_length(),'maximum_increment_bits':max(ctx.weights.values()).bit_length(),'simple_path_upper_bits':int(upper*ctx.scale).bit_length(),'payload':'Python arbitrary precision integers; not uint64/HLS proof','protocol_sha256':sha(out/'protocol.json'),'runs_sha256':sha(out/'runs.json'),'scope':protocol['scope']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
