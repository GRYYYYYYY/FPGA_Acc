"""Freeze existing authenticated CSR/electrical inputs and exact integer lattice."""
import json,shutil
from pathlib import Path
from prepared_csr import read
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from prepared_integer_rc_context import prepare,PreparedIntegerRC
from integer_rc_context import IntegerRC
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';csr=base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr';electrical=base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits';ep=json.loads((base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json').read_text());m,f=read(csr,ep['graph_sha256']);rc=ExactBufferedRC(f,*load(electrical,ep['graph_sha256']));bindings={str(p):sha(p) for folder in (csr,electrical) for p in folder.rglob('*') if p.is_file()};bindings[str(root/'tools/integer_rc_context.py')]=sha(root/'tools/integer_rc_context.py');out=base/'adder_tree_prepared_integer_rc_2026-10-06';digest=prepare(out,rc,bindings);prepared=PreparedIntegerRC(rc,out,digest);original=IntegerRC(rc);assert prepared.scale==original.scale and list(prepared.increments)==original.increments;assert all(prepared.initial(n)==original.initial(n) for n in range(m['nodes']));shutil.copyfile(root/'tools/prepared_integer_rc_context.py',out/'source.py');(out/'verification.json').write_text(json.dumps({'receipt_sha256':digest,'nodes':m['nodes'],'edges':m['edges'],'all_initial_and_increment_values_equal_live_fraction_conversion':True,'source_sha256':sha(out/'source.py'),'scope':'Prepared immutable exact lattice, pinned receipt trust required; no online arbitrary recomputation, board/timing/net benefit claim.'},indent=2)+'\n');print(digest,m['nodes'],m['edges'])
