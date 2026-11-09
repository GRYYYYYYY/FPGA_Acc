"""Graph-specific numerical range analysis; no synthesized hardware claim."""
import json,shutil
from pathlib import Path
from fractions import Fraction
from math import lcm
from pre_route_endpoints import sha
from buffered_rc_context import load
from buffered_rc_node_classes import arc_delay

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');root=b/'exact_buffered_rc_classes_v2';out=b/'exact_integer_width_analysis';out.mkdir()
 protocol=json.loads((root/'protocol.json').read_text());graph=protocol['graph']['sha256'];inputs={str(root/n):sha(root/n) for n in ('receipt.json','protocol.json','electrical_context.json','node_rc_class_ids.bin')}
 sources={n:sha(Path('tools')/n) for n in ('analyze_stereo_exact_integer_width.py','buffered_rc_context.py','buffered_rc_node_classes.py','pre_route_endpoints.py')}
 (out/'source').mkdir()
 for n in sources:shutil.copyfile(Path('tools')/n,out/'source'/n)
 ids,classes,switches=load(root,graph);starts=[r*c/2 for r,c in classes];delays=[arc_delay(classes,switches,c,s) for c in range(len(classes)) for s in switches];scale=1
 for x in starts+delays:scale=lcm(scale,x.denominator)
 encode=lambda v:v.numerator*(scale//v.denominator)
 initial=max(map(encode,starts));increment=max(map(encode,delays));n=len(ids);path_bound=initial+(n-1)*increment;addition_bound=initial+n*increment
 bits=lambda x:max(1,x.bit_length())
 report={'graph_sha256':graph,'inputs':inputs,'sources':sources,'nodes':n,'node_rc_classes':len(classes),'switches':len(switches),'delay_class_entries':len(delays),'exact_common_scale':scale,'scale_bits':bits(scale),'largest_initial_delay_integer':initial,'largest_increment_integer':increment,'initial_bits':bits(initial),'increment_bits':bits(increment),'simple_path_delay_bound_integer':path_bound,'simple_path_bits':bits(path_bound),'one_extra_relaxation_bound_integer':addition_bound,'one_extra_relaxation_bits':bits(addition_bound),'uint64_covers_all_increments_and_relaxations':addition_bound<(1<<64),'uint128_covers_scale_and_all_delay_bounds':max(scale,addition_bound)<(1<<128),'scope':'range proof only for this authenticated finite buffered zero-Cinternal context and simple paths; arbitrary decimal sources/general designs not covered; no kernel synthesis/area/performance proof','implementation_requirements':['Keep class conversion and fractional budget-floor conversion on authenticated host or separately prove intermediate multiplication widths','Represent exact delay and infinity/unknown state separately; unsigned64 additive baseline ABI is insufficient if bounds exceed it','Verify downstream transport, comparisons, heap labels and overflow checks before hardware use','One lattice unit expresses serialized parameter precision, not physical timing accuracy']}
 assert all(sha(k)==h for k,h in inputs.items()) and all(sha(Path('tools')/k)==h for k,h in sources.items())
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('nodes','delay_class_entries','scale_bits','increment_bits','simple_path_bits','one_extra_relaxation_bits','uint64_covers_all_increments_and_relaxations','uint128_covers_scale_and_all_delay_bounds')}),flush=True)
if __name__=='__main__':run()
