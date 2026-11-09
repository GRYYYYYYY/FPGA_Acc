import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'build/map_priority_materialize_v3_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=R/'tools/soft_demand_cpp/map_priority_materialize_v3.cpp';binary=D/'materialize.so';cmd=['c++','-std=c++17','-O3','-fPIC','-shared','-fno-fast-math','-ffp-contract=off',str(source),'-o',str(binary)]
 with (D/'build.log').open('x') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 (D/'receipt.json').write_text(json.dumps({'status':'BUILT_NUMERICAL_CONTRACT_PENDING_NOT_IN_FROZEN_BATCH','command':cmd,'bindings':{str(p):sha(p) for p in [source,Path(__file__),binary]}},indent=2)+'\n');print('MATERIALIZER_BUILT')
if __name__=='__main__':main()
