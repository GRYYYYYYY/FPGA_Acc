#!/usr/bin/env python3
"""Freeze the maintained direct kernel and configurable AXI cosimulation depths.
Depths describe testbench allocations, never restrict the search algorithm.
Run Vitis HLS from the newly created output directory using run.tcl.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

PORTS = {
 'rr': ['rows','edge_ids','destinations','costs','capacities','types','targets'],
 'work': ['labels','known','settled','positions','frontier','scratch','left','right'],
 'paths': ['staged_edges','staged_offsets','accepted_edges','accepted_offsets'],
}
SCALARS = ['nodes','edges','source','target_count','work_budget','context_verified',
 'node_capacity','frontier_capacity','path_capacity','staged_capacity',
 'staged_offset_capacity','accepted_capacity','accepted_offset_capacity']

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--depths',type=Path,required=True)
 parser.add_argument('--testbench',type=Path,required=True)
 parser.add_argument('--output',type=Path,required=True)
 args=parser.parse_args()
 root=Path(__file__).resolve().parents[1]
 depths=json.loads(args.depths.read_text())
 expected={p for ps in PORTS.values() for p in ps}
 if set(depths)!=expected or any(type(v) is not int or v<1 or v>2**63-1 for v in depths.values()):
  parser.error('depths must contain exactly every AXI array port with positive integer allocation sizes')
 if not args.testbench.is_file(): parser.error('testbench must be a file')
 # Never replace an existing experiment, even when it contains partial results.
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
 shutil.copytree(root/'include',out/'include')
 (out/'src').mkdir();(out/'tb').mkdir()
 source=(root/'src/workspace_direct.cpp').read_text()
 signature='routecast::SearchCounters& counters){'
 assert source.count(signature)==1
 directives=[]
 for bundle,ports in PORTS.items():
  for port in ports:
   directives.append(f'#pragma HLS INTERFACE m_axi port={port} offset=slave bundle={bundle} depth={depths[port]}')
 for port in SCALARS:
  directives.append(f'#pragma HLS INTERFACE s_axilite port={port} bundle=control')
 # Unconditionally addressable output metadata avoids conditional ap_vld deadlock.
 for port in ['accepted_edge_count','accepted_target_count']:
  directives.append(f'#pragma HLS INTERFACE m_axi port={port} offset=slave bundle=metadata depth=1')
 for port in ['counters','return']:
  directives.append(f'#pragma HLS INTERFACE s_axilite port={port} bundle=control')
 source=source.replace(signature,signature+'\n'+'\n'.join(directives))
 (out/'src/workspace_direct.cpp').write_text(source)
 shutil.copy2(args.testbench,out/'tb/workspace_direct_tb.cpp')
 (out/'run.tcl').write_text('''set d [file dirname [file normalize [info script]]]
open_project hls_project
set_top routecast_workspace_direct
add_files [file join $d src workspace_direct.cpp] -cflags "-std=c++14 -I[file join $d include]"
add_files -tb [file join $d tb workspace_direct_tb.cpp] -cflags "-std=c++14 -I[file join $d include]"
open_solution u280
set_part {xcu280-fsvh2892-2L-e}
create_clock -period 4.0
csim_design
csynth_design
cosim_design -rtl verilog -tool xsim
exit
''')
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 files=[p for p in out.rglob('*') if p.is_file()]
 protocol={'source_sha256':{str(p.relative_to(out)):sha(p) for p in files},
 'maintained_source_sha256':sha(root/'src/workspace_direct.cpp'),
 'generator_sha256':sha(Path(__file__)), 'port_depths':depths,
 'scope':'configurable testbench AXI allocations; unchanged full search algorithm; no fullgraph/board/benefit proof',
 'host_contract':'authenticate graph/cost and allocated disjoint buffer ranges before context_verified=1; AXI address zero is valid'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 print(out)

if __name__=='__main__': main()
