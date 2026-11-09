"""Cross-language exact SearchResult checks over cyclic sparse physical IDs."""
import json,sys,tempfile,subprocess,random
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph,RREdge
from compact_indexed_sketch import CompactIndexedSketch
from prepared_csr import write,read,U64
binary=Path(sys.argv[1]).resolve()
g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
rng=random.Random(20261004)
with tempfile.TemporaryDirectory() as tmp:
 for case in range(100):
  nodes=dict(g.nodes)
  if case%7==0:nodes[60]=replace(nodes[60],capacity=0)
  extra=tuple(RREdge(rng.choice(list(nodes)),rng.choice(list(nodes)),5,()) for _ in range(15))
  graph=replace(g,nodes=nodes,edges=g.edges+(extra if case!=1 else ()))
  engine=CompactIndexedSketch(graph,node_budget=len(nodes))
  engine.outgoing={n:tuple((eid,dst,None if w is None else (U64-1 if case==1 else rng.choice((0,1,2,U64-1)))) for eid,dst,w in arcs) for n,arcs in engine.outgoing.items()}
  directory=Path(tmp)/str(case);manifest=write(engine,directory);read(directory,graph.sha256,manifest['context_sha256'])
  sources=[n for n in nodes if nodes[n].type=='SOURCE'];sinks=[n for n in nodes if nodes[n].type=='SINK']
  batch_queries=[];batch_expected=[]
  for source in sources:
   for targets in [[s] for s in sinks]+[sinks,list(reversed(sinks)),sinks+sinks]:
    expected=engine.search(source,targets)
    if case==1:assert any(len(path)>1 for path in expected.paths.values()), 'large-cost case must overflow uint64'
    run=subprocess.run([str(binary),str(directory),str(source),*map(str,targets)],capture_output=True,text=True,check=True)
    actual=json.loads(run.stdout)
    batch_queries.append(" ".join(map(str,[source,*targets])))
    batch_expected.append(actual)
    assert actual=={'paths':{str(k):list(v) for k,v in expected.paths.items()},'settled_nodes':expected.settled_nodes,'edge_visits':expected.edge_visits,'budget_exhausted':expected.budget_exhausted},(case,source,targets,actual,expected)
  batch_queries=batch_queries+list(reversed(batch_queries))+batch_queries
  batch_expected=batch_expected+list(reversed(batch_expected))+batch_expected
  batch=subprocess.run([str(binary),str(directory),'--batch'],input="\n".join(batch_queries)+"\n",capture_output=True,text=True,check=True)
  assert [json.loads(line) for line in batch.stdout.splitlines()]==batch_expected
  if case==0:
   bad=subprocess.run([str(binary),str(directory),'999999',str(sinks[0])],capture_output=True)
   assert bad.returncode!=0
   (directory/'dest_ranks.bin').write_bytes((U64).to_bytes(8,'little')*len(graph.edges))
   bad=subprocess.run([str(binary),str(directory),str(sources[0]),str(sinks[0])],capture_output=True)
   assert bad.returncode!=0
print('100 cases including duplicate/reversed targets and triple repeated batch: full SearchResult parity passed')
