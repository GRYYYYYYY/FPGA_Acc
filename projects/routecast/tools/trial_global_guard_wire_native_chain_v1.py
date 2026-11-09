import subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for name in ('trial_global_guard_wire_native_reload_v1.py','verify_global_guard_wire_reconciled_dump_v1.py','trial_global_guard_wire_canonical_v1.py','verify_global_guard_wire_canonical_v1.py'):
 subprocess.run(['python3',str(R/'tools'/name)],cwd=R,check=True)
