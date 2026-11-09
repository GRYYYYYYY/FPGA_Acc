import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for index in range(4):
 subprocess.run(['python3',str(R/'tools/trial_critical_owner_native_reload_v1.py'),str(index)],cwd=R,check=True)
