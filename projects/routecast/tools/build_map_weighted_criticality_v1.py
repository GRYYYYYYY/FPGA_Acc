"""Separate ABI/library; legacy exact primitive unchanged."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'build/map_weighted_criticality_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=R/'tools/soft_demand_cpp/map_weighted_criticality_v1.cpp';old=R/'tools/soft_demand_cpp/criticality_tree_exact_v2.cpp';design=R/'experiments/wbuart_map_weighted_primitive_design_v1_2026-10-20/protocol.json';v=json.loads(design.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());cmd=['c++','-std=c++17','-O3','-fPIC','-shared',str(source),'-o',str(D/'search.so')]
 with (D/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 (D/'receipt.json').write_text(json.dumps({'status':'WEIGHTED_PRIORITY_PRIMITIVE_BUILT_CONTRACT_PENDING','command':cmd,'binary':str(D/'search.so'),'binary_sha256':sha(D/'search.so'),'bindings':{str(p):sha(p) for p in [Path(__file__),source,old,design]},'scope':'NonnegativeH priority bias, not admissible/optimal/native-equivalent; H0 parity and reference validation pending.'},indent=2)+'\n');print('MAP_WEIGHTED_PRIMITIVE_BUILD_PASS')
if __name__=='__main__':main()
