"""Frozen12 development frames:3widths x(source+3independent swaps), no route search."""
import json,shlex,subprocess,resource,time,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from decimal import Decimal
from pre_route_endpoints import sha,extract
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def graph_domain(path,width):
 stack=[];nodes=0;edges=0;types=Counter();rc=Counter();caps=Counter();switches={};kinds={};channel=None
 for event,x in ET.iterparse(path,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='channel' and parent is not None and parent.tag=='channels':channel=dict(x.attrib)
  elif x.tag=='switch' and parent is not None and parent.tag=='switches':
   sid=int(x.get('id'));assert sid not in switches;t=x.find('timing');vals={k:Decimal(t.get(k,'0')) for k in ['R','Cin','Cout','Tdel']};assert all(v.is_finite() and v>=0 for v in vals.values());raw=vals['Tdel']*10**18;assert raw==raw.to_integral_value();switches[sid]=dict(type=x.get('type'),name=x.get('name'),Tdel_1e18=int(raw),timing={k:str(v) for k,v in vals.items()});parent.remove(x);x.clear()
  elif x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(x.get('id'));assert n==nodes;nodes+=1;kind=x.get('type');types[kind]+=1;cap=int(x.get('capacity'));assert cap>0;caps[kind+':'+str(cap)]+=1;t=x.find('timing');r,c=Decimal(t.get('R')),Decimal(t.get('C'));assert r.is_finite() and c.is_finite() and r>=0 and c>=0;rc[str(r)+','+str(c)]+=1
   if kind in ['SOURCE','SINK']:kinds[n]=kind
   parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':assert 0<=int(x.get('src_node'))<nodes and 0<=int(x.get('sink_node'))<nodes and int(x.get('switch_id')) in switches;edges+=1;parent.remove(x);x.clear()
  stack.pop()
 assert channel is not None and int(channel['chan_width_max'])==width and nodes>0 and edges>0;assert all(all(Decimal(v)==0 for v in key.split(',')) for key in rc)
 return dict(graph_sha256=sha(path),nodes=nodes,edges=edges,node_types=dict(types),capacity_domain=dict(caps),node_RC_histogram=dict(rc),all_node_RC_zero=True,switches=switches,channel=channel),kinds

def compare(ep,terminal,encoding,domain,kinds,source):
 e=read(ep);expected=Counter();seen=set();header=None
 for line in terminal.read_text().split('\n'):
  if not line:continue
  t=shlex.split(line)
  if t[0]=='H':assert header is None;header=tuple(map(int,t[1:]));continue
  assert t[0]=='N';name=t[2];assert name not in seen;seen.add(name);clock=t[5]
  if encoding=='raw_uint8':assert clock in ('\x00','\x01');clock=ord(clock)
  else:assert encoding=='integer01' and clock in ('0','1');clock=int(clock)
  terms=list(map(int,t[7:]));assert len(terms)==int(t[6]) and kinds[terms[0]]=='SOURCE' and all(kinds[n]=='SINK' for n in terms[1:]);assert (clock==1)==(name=='clk')
  if name!='clk':expected.update((name,terms[0],sink) for sink in terms[1:])
 assert header==(domain['nodes'],domain['edges'],5920);names={int(n):name for n,name in e['net_names'].items()};assert set(names.values())==seen and e['net_names']==source['net_names'];actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in e['connections']);assert expected==actual and sum(actual.values())==15616
 old={q['connection_id']:q for q in source['connections']};assert [q['connection_id'] for q in e['connections']]==list(range(15616))
 for q in e['connections']:assert q['net_id']==old[q['connection_id']]['net_id']
 assert e['graph_sha256']==domain['graph_sha256'];return e

def main():
 out=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19';out.mkdir(exist_ok=False);build=R/'build/native_external_preroute_context_v3_2026-10-19';br=read(build/'receipt.json');binary=build/'native_preroute_context';assert br['exit_code']==0 and sha(binary)==br['binary_sha256'];assert all(sha(p)==h for p,h in read(build/'protocol.json')['bindings'].items());src=R/'experiments/prospective_external_family_development_place_v1_2026-10-19';swaps=R/'experiments/prospective_external_family_development_swaps_v1_2026-10-19';sv=read(swaps/'verification.json');assert all(sha(p)==h for p,h in sv['bindings'].items());parent=R/'experiments/prospective_external_family_preroute_context_v2_2026-10-19';basecmd=read(parent/'protocol.json')['command'];sourceep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';source=read(sourceep);frames=['source','episode_01','episode_02','episode_03'];jobs=[]
 for width in [96,128,160]:
  graph=Path(source['inputs']['graph']['path']) if width==128 else out/f'w{width:03d}'/'source/rr_graph.xml'
  for frame in frames:
   d=out/f'w{width:03d}'/frame;d.mkdir(parents=True);place=src/'source.place' if frame=='source' else swaps/frame/'design.place';reused=width==128;cmd=None
   if not reused:
    cmd=list(basecmd);cmd[0]=str(binary);cmd[1]=str(d/'native_terminals.txt');cmd[cmd.index('--place_file')+1]=str(place);cmd[cmd.index('--route_chan_width')+1]=str(width);cmd[cmd.index('--place_chan_width')+1]=str(width);i=cmd.index('--write_rr_graph');del cmd[i:i+2];cmd += ['--write_rr_graph' if frame=='source' else '--read_rr_graph',str(graph)]
   endpoint=sourceep if reused and frame=='source' else swaps/frame/'endpoints.json' if reused else d/'endpoints.json';terminal=parent/'native_terminals.txt' if reused and frame=='source' else swaps/frame/'native_terminals.txt' if reused else d/'native_terminals.txt';jobs.append(dict(case=f'w{width:03d}/{frame}',width=width,frame=frame,directory=str(d),place=str(place),graph=str(graph),endpoint=str(endpoint),native_terminal=str(terminal),clock_encoding='raw_uint8' if reused else 'integer01',reuse_existing_verified_inputs=reused,command=cmd))
 paths=[build/'receipt.json',build/'protocol.json',binary,src/'independent_verification_v1.json',swaps/'verification.json',swaps/'selection.json',sourceep,Path(__file__).resolve()];bindings={str(p):sha(p) for p in paths};protocol=dict(status='FIXED12_ROUTE_FREE_DEVELOPMENT_INPUT_JOBS',jobs=jobs,bindings=bindings,policy='All96/128/160widths and source+three fixed swaps retained. Width128 previously verified inputs are referenced with explicit paid dependency receipts, never free. New graph/terminal jobs use native init/load/device/terminal-only functions; no route search or trees. No replacement for failed frames.',source_semantic_scope='Known conditional-reset and explicit-ground functional certificates; unrestricted HDL/default-X scopes remain separate.',family_role='UNKNOWN-history development input preparation, not strict unseen or a frozen complete prediction/utility protocol.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2));domains={};results=[]
 for job in jobs:
  d=Path(job['directory']);width=job['width'];tick=time.perf_counter();pre={str(p):sha(p) for p in [src/'design.net',src/'design.blif',Path(job['place'])]}
  if not job['reuse_existing_verified_inputs']:
   def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
   with (d/'native.log').open('x') as log:run=subprocess.run(job['command'],cwd=d,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
   if run.returncode:raise RuntimeError(f'Native input job failed, preserved: {job["case"]} exit{run.returncode}')
   text=(d/'native.log').read_text();assert 'PREROUTE_CONTEXT_EXPORTED_NO_ROUTE_TREES' in text and 'Completed placement consistency check successfully.' in text;endpoint,report=extract(src/'design.net',Path(job['place']),Path(job['graph']));Path(job['endpoint']).write_text(json.dumps(endpoint,indent=2)+'\n');(d/'mapping_report.json').write_text(json.dumps(report,indent=2)+'\n')
  if width not in domains:
   domain,kinds=graph_domain(Path(job['graph']),width);domains[width]=(domain,kinds);(out/f'w{width:03d}'/'graph_domain.json').write_text(json.dumps(domain,indent=2)+'\n')
  domain,kinds=domains[width];e=compare(Path(job['endpoint']),Path(job['native_terminal']),job['clock_encoding'],domain,kinds,source);assert all(sha(p)==h for p,h in pre.items());assert not list(d.glob('*.route'));files=[Path(job['place']),Path(job['graph']),Path(job['endpoint']),Path(job['native_terminal']),out/'protocol.json',out/f'w{width:03d}'/'graph_domain.json'];files += [d/'native.log',d/'mapping_report.json'] if not job['reuse_existing_verified_inputs'] else [parent/'receipt.json'] if job['frame']=='source' else [swaps/'verification.json'];frame=dict(schema='ROUTECAST_EXTERNAL_GRAPH_ENDPOINT_FRAME_V1',case=job['case'],width=width,frame=job['frame'],endpoint=job['endpoint'],native_terminal=job['native_terminal'],clock_encoding=job['clock_encoding'],place=job['place'],graph=job['graph'],graph_sha256=domain['graph_sha256'],graph_nodes=domain['nodes'],graph_edges=domain['edges'],connections=15616,nets=5920,source_inputs_unchanged=True,reused_paid_dependency=job['reuse_existing_verified_inputs'],input_preparation_and_verification_seconds=time.perf_counter()-tick,route_search_executed=False,strict_unseen_admitted=False,bindings={str(p):sha(p) for p in files});fp=d/'verification.json';fp.write_text(json.dumps(frame,indent=2)+'\n');results.append(dict(frame_verification=str(fp),sha256=sha(fp),case=job['case'],width=width,frame=job['frame'],connections=15616,reused_paid_dependency=job['reuse_existing_verified_inputs']));(out/'progress.json').write_text(json.dumps(dict(rows=results),indent=2));print('WIDTH_FRAME_INPUT_VERIFIED',job['case'],domain['nodes'],domain['edges'],'reused',job['reuse_existing_verified_inputs'],flush=True)
 assert len(results)==12 and len({domains[w][0]['graph_sha256'] for w in domains})==3;assert all(sha(p)==h for p,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(status='ALL12_FIXED_WIDTH_LAYOUT_INPUTS_NATIVE_TERMINALS_XML_DOMAINS_AND_CID_IDENTITIES_VERIFIED',rows=results,graphs={str(w):domain for w,(domain,kinds) in domains.items()},bindings={str(out/'protocol.json'):sha(out/'protocol.json'),**{r['frame_verification']:r['sha256'] for r in results}},strict_unseen_admitted=False,new_source_or_target_route_search=False,current_timing_and_floors_for_all12_ready=False,scope='Graph/placement/endpoints only. Different widths retain independent graph epochs. All reused source128 preparation costs remain paid upstream dependencies, no matched timing or quality gain.'),indent=2))
if __name__=='__main__':main()
