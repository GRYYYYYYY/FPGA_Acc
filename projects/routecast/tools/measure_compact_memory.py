"""Separate Python allocation measurement; never use traced timings as performance."""
import argparse,json,tracemalloc,resource
from pathlib import Path
from rr_graph import read_rr_graph
from semantic_sketch import Sketch
from compact_indexed_sketch import CompactIndexedSketch
from pre_route_endpoints import sha
p=argparse.ArgumentParser();p.add_argument('--engine',choices=['original','compact'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
ep=json.loads(Path('experiments/pre_route_endpoints_2026-10-04/diffeq_endpoints.json').read_text());g=read_rr_graph(ep['inputs']['graph']['path']);assert g.sha256==ep['graph_sha256']
tracemalloc.start();engine=(Sketch if a.engine=='original' else CompactIndexedSketch)(g,'rr_length_switch',len(g.nodes));current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
r={'engine':a.engine,'graph_sha256':g.sha256,'graph_nodes':len(g.nodes),'graph_edges':len(g.edges),'retained_python_allocations_bytes':current,'peak_python_allocations_bytes':peak,'process_peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'source_sha256':{n:sha(Path(__file__).with_name(n)) for n in ('measure_compact_memory.py','compact_indexed_sketch.py','semantic_sketch.py','rr_graph.py')},'scope':'physical graph search engine allocations after graph load; excludes immutable RR graph, quotient, repair, frontend and ledger; instrumentation not used for timing'}
a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
