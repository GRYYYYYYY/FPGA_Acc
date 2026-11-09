"""Fixed first-net native snapshot differential and bounded CPU timing probe."""
import collections,csv,hashlib,json,struct,time,xml.etree.ElementTree as E
from pathlib import Path
from decimal import Decimal
from shared_tree_budget_repair import repair as reference
from shared_tree_budget_repair_implicit import repair as candidate
from check_implicit_tree_budget_repair import normalized
R=Path(__file__).resolve().parents[1];P=R/'work/implicit_native_tree_probe_20261017'
def rows(p):return list(csv.DictReader(Path(p).open()))
def main():
 P.mkdir(exist_ok=False);protocol=R/'work/native_instrumented_compound_repeat_20261016/protocol.json';case=json.loads(protocol.read_text())['cases'][0]
 D=R/'work/native_instrumented_compound_repeat_20261016/sweep/ex5p';snapshot=D/'initial'
 nodes=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.nodes').read_bytes()));edges=list(struct.iter_unpack('<IHH',Path(case['input_prefix']+'.edges').read_bytes()));resources=list(struct.iter_unpack('<HHHHII',Path(case['input_prefix']+'.resources').read_bytes()));die=[v[0] for v in struct.iter_unpack('<H',Path(case['topology_prefix']+'.node_die').read_bytes())]
 trees={};sources={}
 for v in rows(snapshot/'route.route_trees.csv'):
  net=int(v['net_id']);trees.setdefault(net,{})[int(v['child'])]=int(v['parent']);sources[net]=int(v['source'])
 length=[0]*len(nodes)
 for _,e in E.iterparse(Path(case['native_case'])/'rr_graph.xml',events=('end',)):
  if e.tag=='node':
   a=e.attrib;l=e.find('loc')
   if a['type'] in ['CHANX','CHANY'] and a.get('direction')!='NONE':length[int(a['id'])]=1+int(l.attrib['xhigh'])-int(l.attrib['xlow'])+int(l.attrib['yhigh'])-int(l.attrib['ylow'])
   e.clear()
  elif e.tag=='edge':e.clear()
 net=min(trees,key=lambda n:(-sum(length[v] for v in trees[n]),n));taskrows={int(v['id']):v for v in rows(case['connections'])};obs={int(v['task_id']):v for v in rows(snapshot/'observation.output.csv')}
 owners=collections.Counter(v for other,t in trees.items() if other!=net for v in t);allowed=[owners[v]<r[1] for v,r in enumerate(resources)]
 baseline=rows(case['native_tree']);baseline_cross=sum(die[int(v['child'])]!=die[int(v['parent'])] for v in baseline);budget=baseline_cross-sum(die[v]!=die[u] for other,t in trees.items() if other!=net for v,u in t.items())
 quality=json.loads((snapshot/'native_validation/validation.json').read_text());limit=int(max(Decimal(str(case['baseline_cpd_ns'])),Decimal(str(quality['critical_path_delay_ns'])))*1000)
 tasks=[dict(id=t,sink=int(taskrows[t]['sink']),delay_budget=max(0,int(obs[t]['delay_ps'])+limit+int(obs[t]['slack_ps'])),max_hops=int(taskrows[t]['max_hops'])) for t in sorted([t for t,v in taskrows.items() if int(v['net_id'])==net],key=lambda t:(-int(obs[t]['criticality_q']),t))]
 results=[];expected=None
 for name,fn in [('reference',reference),('implicit',candidate),('implicit',candidate),('reference',reference)]:
  start=time.monotonic_ns();answer=fn(nodes,edges,allowed,length,die,sources[net],tasks,budget);elapsed=time.monotonic_ns()-start
  value=normalized(answer)
  if expected is None:expected=value
  else:assert value==expected,name
  results.append(dict(arm=name,wall_ns=elapsed,status=answer['status'],tasks_searched=len(answer['steps'])))
  (P/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
 sources=[protocol,snapshot/'route.route_trees.csv',snapshot/'observation.output.csv',Path(__file__),*[R/'tools'/f for f in ['shared_tree_budget_repair.py','shared_tree_budget_repair_implicit.py','implicit_tree_budget_search.py','delay_crossing_bounded_wire_search.py']]]
 report=dict(status='fixed_native_first_net_equivalent_arms_timed',net=net,requests=len(tasks),nodes=len(nodes),edges=len(edges),outcomes=results,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},scope='One fixed original initial snapshot; balanced ABBA order, two observations per arm. No full sweep, full pipeline speedup, native STA recomputation or hardware claim.',research_complete=False,adopted=False)
 (P/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
