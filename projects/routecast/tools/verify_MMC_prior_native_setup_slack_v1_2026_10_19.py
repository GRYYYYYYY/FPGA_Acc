"""Native float/atom-min slack checks and graph-rooted mapping for all model CIDs."""
import pathlib,json,hashlib,struct,math
from collections import defaultdict,Counter
from rooted_canonical_native_reload_v2 import selected_geometry
from rooted_native_sink_pin_v1 import root
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_prior_setup_slack_export_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def value(bits):return struct.unpack('<f',struct.pack('<I',bits))[0]
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def checked(row,key,bkey):
 x=value(row[bkey]);assert (row[key] is None)==(not math.isfinite(x))
 if math.isfinite(x):assert bits(row[key])==row[bkey]
 return x

def main():
 rp=O/'receipt.json';receipt=json.loads(rp.read_text());assert receipt['exit_code']==0 and receipt['full_pass'] and receipt['source_route_bytes_identical'] and receipt['source_packed_post_bytes_identical']
 for p,h in receipt['bindings'].items():assert sha(pathlib.Path(p))==h
 rows={};native_counts=Counter();export=O/'routecast_cluster_criticality.jsonl'
 for line in export.open():
  r=json.loads(line);key=(r['net_id'],r['net_pin_index']);assert key not in rows;slack=checked(r,'setup_slack_s','setup_slack_float32_bits');delay=value(r['native_route_delay_float32_bits']);assert math.isfinite(delay) and delay>=0 and bits(r['native_route_delay_s'])==r['native_route_delay_float32_bits'];expected=math.inf
  for ap in r['atom_pins']:
   x=checked(ap,'setup_slack_s','setup_slack_float32_bits')
   if x<expected:expected=x
  assert bits(expected)==r['setup_slack_float32_bits'];rows[key]=r;native_counts['rows']+=1;native_counts['ignored']+=r['ignored_net'];native_counts['clock']+=r['clock_sink'];native_counts['nonfinite' if not math.isfinite(slack) else ('negative' if slack<0 else ('zero' if slack==0 else 'positive'))]+=1
 S=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';source=json.loads(S.read_text());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=pathlib.Path(g['previous_endpoint']);metadata=json.loads(ep.read_text());graph=pathlib.Path(metadata['inputs']['graph']['path']);identity=R/'experiments/ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10/cold/canonical/mmc/identity.jsonl';native={r['name']:r for r in map(json.loads,identity.read_text().splitlines())};wanted={q['sink'] for q in source['records']};nodes,grid,_=selected_geometry(graph,wanted);pinmap={}
 for name,r in native.items():
  grouped=defaultdict(list)
  for p in r['pins']:
   if p['index']>0:grouped[tuple(p[k] for k in ['x','y','layer','class'])].append(p)
  pinmap[name]=(r,grouped)
 mapped=[];used=set();stats=Counter();max_abs_delay_error=0.
 for q in source['records']:
  name=metadata['net_names'][str(q['net_id'])];nr,grouped=pinmap[name];node=nodes[q['sink']];assert node['type']=='SINK';_,x,y,layer=root(node,grid);site=(x,y,layer,int(node['loc']['ptc']));pins=grouped[site];assert len(pins)==1;pin=pins[0];key=(nr['net_id'],pin['index']);assert key not in used;used.add(key);r=rows[key];assert r['net']==name and r['block']==pin['block'] and r['port']==pin['port'] and r['bit']==pin['bit'] and not r['ignored_net'];native_delay=value(r['native_route_delay_float32_bits']);model=q['answer']['delay']/10**18;error=abs(native_delay-model);tolerance=(len(q['answer']['physical_edge_ids'])+1)*2**-23*max(native_delay,model,1e-18);assert error<=tolerance;max_abs_delay_error=max(max_abs_delay_error,error);slack=value(r['setup_slack_float32_bits']);category='nonfinite' if not math.isfinite(slack) else ('negative' if slack<0 else ('zero' if slack==0 else 'positive'));stats[category]+=1;stats['clock']+=r['clock_sink'];mapped.append(dict(connection_id=q['connection_id'],model_NET_id=q['net_id'],native_NET_id=key[0],native_sink_index=key[1],setup_slack_s=r['setup_slack_s'],setup_slack_float32_bits=r['setup_slack_float32_bits'],native_route_delay_float32_bits=r['native_route_delay_float32_bits'],clock_sink=r['clock_sink'],connected_atom_pins=len(r['atom_pins'])))
 assert len(mapped)==len(used)==115572;unmapped=set(rows)-used;assert len(unmapped)==3901 and all(rows[k]['ignored_net'] for k in unmapped)
 out=O/'model_connection_setup_slacks.json';out.write_text(json.dumps(mapped,separators=(',',':'))+'\n');report=O/'report_timing.setup.rpt';summary=[]
 for line in report.read_text().splitlines():
  if any(t in line for t in ['data required time','data arrival time','slack (']):summary.append(' '.join(line.split()))
  if len(summary)==5:break
 bindings={str(p):sha(p) for p in [rp,export,S,ep,graph,identity,out,report,pathlib.Path(__file__).resolve()]}
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL115572_NATIVE_PRIOR_SETUP_SLACK_IDENTITIES_FLOAT_BITS_AND_ATOM_MIN_AGGREGATES_PASS',export_rows=len(rows),mapped_model_connections=len(mapped),extra_ignored_pins=len(unmapped),native_counts=dict(native_counts),mapped_slack_counts=dict(stats),max_native_vs_exact_model_route_delay_error_s=max_abs_delay_error,first_report_timing_summary=summary,bindings=bindings,scope='Actual raw STA slack at prior source analysis constraints, not inferred from criticality. Negative/unconstrained slack gives no spendable margin; required-time tags and constraint semantics still needed before a new timing budget policy. Individual slack cannot be independently allocated to multiple changed connections.'),f,indent=2)
 print('SLACK IDENTITY PASS',dict(stats),'extra ignored',len(unmapped),'report',summary,flush=True)
if __name__=='__main__':main()
