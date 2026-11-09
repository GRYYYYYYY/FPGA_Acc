import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for name in ('trial_complete_wire_native_reload_v2.py','verify_complete_wire_reconciled_dump_v2.py','trial_complete_wire_canonical_v2.py','verify_complete_wire_canonical_v2.py'):
 subprocess.run(['python3',str(R/'tools'/name)],cwd=R,check=True)
