import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for index in range(4):
 for script in ('verify_critical_owner_reconciled_dump_v1.py','trial_critical_owner_canonical_v1.py','verify_critical_owner_canonical_v1.py'):
  subprocess.run(['python3',str(R/'tools'/script),str(index)],cwd=R,check=True)
