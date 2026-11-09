"""Complete real-graph exact equivalence of metadata-cached RC preparation."""
import json,time,importlib.util
from pathlib import Path
from rr_graph import read_rr_graph
from buffered_delay_cost import BufferedDelayCost
from pre_route_endpoints import sha
out=Path('experiments/frisc_delay_cost_preparation_profile_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files=['work/frisc_graph_capture_2026-10-05/rr_graph.xml','experiments/frisc_incremental_budget_profiled_2026-10-05/delay_cost.py','tools/buffered_delay_cost.py'];inputs={p:sha(p) for p in files};g=read_rr_graph(files[0]);spec=importlib.util.spec_from_file_location('old_buffered_cost',files[1]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);t=time.monotonic();old=module.BufferedDelayCost(g);old_s=time.monotonic()-t;t=time.monotonic();new=BufferedDelayCost(g);new_s=time.monotonic()-t;assert old.denominator==new.denominator and old.weights==new.weights and old.nodes==new.nodes;assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());r={'graph_sha256':g.sha256,'edge_count':len(g.edges),'all_integer_weights_and_common_denominator_exact':True,'all_node_rc_parameters_exact':True,'old_prepare_s':old_s,'metadata_cached_prepare_s':new_s,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'all graph arcs exact preparation equivalence, concurrent host CPU wall costs descriptive; no end-to-end/hardware performance claim'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
