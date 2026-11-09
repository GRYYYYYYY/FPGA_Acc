import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'build/exact_min_sum_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=R/'tools/soft_demand_cpp/exact_min_sum_v1.cpp';design=R/'experiments/wbuart_exact_aggregate_solver_design_v1_2026-10-20/protocol.json';assert all(sha(p)==h for p,h in json.loads(design.read_text())['bindings'].items());binary=D/'minsum.so';cmd=['c++','-std=c++17','-O3','-fPIC','-shared',str(source),'-o',str(binary)]
 with (D/'build.log').open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 if r.returncode:(D/'failure.json').write_text(json.dumps({'exit_status':r.returncode,'stage':'compile'})+'\n');raise RuntimeError('compile failed')
 (D/'receipt.json').write_text(json.dumps({'status':'CHECKED_INTEGER_MIN_SUM_KERNEL_BUILT_NUMERIC_CONTRACT_PENDING','command':cmd,'bindings':{str(p):sha(p) for p in [Path(__file__),source,design,binary]}},indent=2)+'\n');print('EXACT_MIN_SUM_BUILT')
if __name__=='__main__':main()
