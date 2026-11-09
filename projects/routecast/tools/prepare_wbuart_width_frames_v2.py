"""Twelve source/swap input contexts with native-vs-XML terminal verification."""
import datetime,hashlib,json,os,resource,shlex,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import extract,PhysicalMapContext,physical_maps,placements
from prepare_external_width_frame_inputs_v1_2026_10_19 import graph_domain
R=Path(__file__).resolve().parents[1];S=R/'experiments/wbuart_development_place_v1_2026-10-20';C=R/'experiments/wbuart_input_cohort_v1_2026-10-20';O=R/'experiments/wbuart_width_frames_v2_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
 with p.open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);cp=json.loads((C/'protocol.json').read_text());sel=json.loads((C/'selection.json').read_text());assert cp['widths']==[96,128,160] and len(sel['rows'])==3
 for n,h in cp['bindings'].items():assert sha(Path(n))==h
 for row in sel['rows']:assert sha(Path(row['place']))==row['sha256']
 build=R/'build/native_external_preroute_context_v3_2026-10-19';br=json.loads((build/'receipt.json').read_text());binary=build/'native_preroute_context';assert br['exit_code']==0 and sha(binary)==br['binary_sha256']
 for d in [br,json.loads((build/'protocol.json').read_text())]:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 placeprotocol=json.loads((S/'protocol.json').read_text());arch=Path(placeprotocol['command'][1]);frames=[('source',S/'source.place')]+[(f'episode_{r["episode"]:02d}',Path(r['place'])) for r in sel['rows']]
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py',R/'tools/prepare_external_width_frame_inputs_v1_2026_10_19.py',C/'protocol.json',C/'selection.json',S/'design.net',S/'design.blif',binary,build/'receipt.json',arch,*[p for _,p in frames]]}
 save(O/'protocol.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':bindings,'widths':cp['widths'],'frames':[n for n,_ in frames],'role':'Input-only development. vpr_init/load packing/create device/load placement/init_route_structs export, require route_trees empty. No route search or new placement. Each width binds own graph SHA and endpoint epoch.','policy':'No width/pair replacement; retain failures; strict unseen false; original cohort and gates unchanged. Full XML nonclock endpoint multiset verified before native ignored-net partition. Routing view excludes only native ignored nonclock nets with full CID provenance retained. No route labels used for this input metadata decision.'})
 results=[];domains={};env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for w in cp['widths']:
  graph=O/f'w{w:03d}/source/rr_graph.xml';context=None;source=None
  for name,place in frames:
   d=O/f'w{w:03d}'/name;d.mkdir(parents=True);term=d/'native_terminals.txt';cmd=[str(binary),str(term),str(arch),str(S/'design.blif'),'--place','--net_file',str(S/'design.net'),'--place_file',str(place),'--place_algorithm','criticality_timing','--timing_analysis','on','--place_chan_width',str(w),'--route_chan_width',str(w),'--num_workers','1','--seed','1']
   cmd+=['--write_rr_graph' if name=='source' else '--read_rr_graph',str(graph)];save(d/'protocol.json',{'command':cmd,'width':w,'frame':name,'placement_sha256':sha(place),'timeout_seconds':120,'AS_limit_bytes':8*2**30});start=time.perf_counter()
   def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
   with (d/'native.log').open('x') as f:p=subprocess.run(cmd,cwd=d,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit,timeout=120)
   if p.returncode!=0:
    save(d/'failure.json',{'exit_status':p.returncode,'retained_no_replacement':True});raise RuntimeError('Native context failed; retained')
   text=(d/'native.log').read_text();assert 'PREROUTE_CONTEXT_EXPORTED_NO_ROUTE_TREES' in text and 'Completed placement consistency check successfully.' in text;assert not list(d.glob('*.route'))
   if name=='source':
    domain,kinds=graph_domain(graph,w);domains[str(w)]=domain;context=PhysicalMapContext(graph);types,grid,_=physical_maps(graph);source_locations=placements(place,sha(S/'design.net'))
   else:
    row=next(r for r in sel['rows'] if name==f'episode_{r["episode"]:02d}');current=placements(place,sha(S/'design.net'));changed={n for n in current if current[n]!=source_locations[n]};assert changed==set(row['blocks'])
    physical=[]
    for block in row['blocks']:
     for loc in [source_locations[block],current[block]]:
      x,y,sub,layer,_=loc;tid,wo,ho=grid[x,y,layer];assert wo==ho==0;physical.append((types[tid]['name'],sub,layer))
    assert len(set(physical))==1 and physical[0]==('clb',0,0)
   e,report=extract(S/'design.net',place,graph,physical_context=context);save(d/'endpoints.json',e);save(d/'mapping_report.json',report);clocknames={x['net'] for x in e['excluded_nets']};assert clocknames=={'i_clk'}
   expected=Counter();seen=set();header=None;native_clock_sinks=0;flags={}
   for line in term.read_text().splitlines():
    if not line:continue
    t=shlex.split(line)
    if t[0]=='H':assert header is None;header=tuple(map(int,t[1:]));continue
    assert t[0]=='N';n=t[2];assert n not in seen;seen.add(n);flags[n]={'ignored':int(t[3]),'global':int(t[4])};clock=int(t[5]);terms=list(map(int,t[7:]));assert clock in (0,1) and bool(clock)==(n in clocknames) and len(terms)==int(t[6]);assert kinds[terms[0]]=='SOURCE' and all(kinds[v]=='SINK' for v in terms[1:])
    if n in clocknames:native_clock_sinks+=len(terms)-1
    else:expected.update((n,terms[0],v) for v in terms[1:])
   names={int(i):n for i,n in e['net_names'].items()};actual=Counter((names[q['net_id']],q['source'],q['sink']) for q in e['connections']);assert expected==actual and set(names.values())==seen and header==(domain['nodes'],domain['edges'],len(seen));assert native_clock_sinks==sum(v['sink_pins'] for v in e['excluded_nets'])
   # Preserve full declared mapping, then establish the native-routed input domain.
   ignored={n for n,v in flags.items() if v['ignored'] and n not in clocknames};assert ignored=={'o_wb_stall','o_wb_data[31]'}
   assert all(v['global']==0 for n,v in flags.items() if n not in clocknames)
   declared_connections=len(e['connections']);full_e=e;routed=[];omitted=[]
   for q in full_e['connections']:
    n=names[q['net_id']]
    if n in ignored:omitted.append(dict(q,net_name=n,reason='native_net_is_ignored_nonclock'))
    else:routed.append(dict(q,connection_id=len(routed),full_connection_id=q['connection_id']))
   assert len(omitted)==2 and declared_connections==len(routed)+len(omitted)
   e=dict(full_e,connections=routed,excluded_nets=full_e['excluded_nets']+[{'net':n,'net_id':next(i for i,name in names.items() if name==n),'reason':'native_net_is_ignored_nonclock','sink_pins':sum(x['net_name']==n for x in omitted)} for n in sorted(ignored)],connection_id_domain='dense_native_routed_nonclock_view_with_full_connection_id_provenance')
   save(d/'routing_endpoints.json',e);save(d/'native_ignored_partition.json',{'flags':flags,'ignored_nonclock_names':sorted(ignored),'omitted_connections':omitted,'declared_connections':declared_connections,'routing_connections':len(routed),'full_XML_multiset_matches_all_nonclock_native_terms':True})
   routed_native=Counter({k:v for k,v in expected.items() if k[0] not in ignored});assert routed_native==Counter((names[q['net_id']],q['source'],q['sink']) for q in routed)
   assert [q['connection_id'] for q in e['connections']]==list(range(len(e['connections'])))
   if name=='source':source=e;affected=0
   else:
    assert e['net_names']==source['net_names'] and len(e['connections'])==len(source['connections']);old={q['connection_id']:q for q in source['connections']};assert all(q['net_id']==old[q['connection_id']]['net_id'] for q in e['connections']);affected=sum((q['source'],q['sink'])!=(old[q['connection_id']]['source'],old[q['connection_id']]['sink']) for q in e['connections'])
   v={'status':'NATIVE_TERMINALS_XML_ENDPOINT_MULTISET_AND_PLACEMENT_VERIFIED','width':w,'frame':name,'graph_sha256':domain['graph_sha256'],'graph_nodes':domain['nodes'],'graph_edges':domain['edges'],'external_nets':len(seen),'connections':len(e['connections']),'declared_connections':declared_connections,'ignored_nonclock_connections':len(omitted),'clock_sinks_excluded':native_clock_sinks,'affected_connections':affected,'seconds':time.perf_counter()-start,'new_route_search':False,'strict_unseen_admitted':False,'bindings':{str(p):sha(p) for p in [d/'protocol.json',term,d/'native.log',d/'endpoints.json',d/'mapping_report.json',d/'routing_endpoints.json',d/'native_ignored_partition.json',place,graph]}};save(d/'verification.json',v);results.append({'width':w,'frame':name,'connections':len(e['connections']),'affected_connections':affected,'verification':str(d/'verification.json'),'sha256':sha(d/'verification.json')});(O/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print('WBUART_FRAME_VERIFIED',w,name,len(e['connections']),affected,flush=True)
 assert len(results)==12 and len({v['graph_sha256'] for v in domains.values()})==3
 for n,h in bindings.items():assert sha(Path(n))==h
 save(O/'verification.json',{'status':'ALL12_WBUART_WIDTH_LAYOUT_CONTEXTS_AND_NATIVE_IGNORED_PARTITION_VERIFIED_NO_ROUTE_SEARCH','rows':results,'graphs':domains,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json'),**{v['verification']:v['sha256'] for v in results}},'strict_unseen_admitted':False,'timing_floors_budgets_all_ready':False,'complete_prediction_utility_protocol_frozen':False})
if __name__=='__main__':main()
