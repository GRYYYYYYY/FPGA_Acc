"""Run the unchanged budget auditor with explicit repository cwd."""
from pathlib import Path
import hashlib
import os
import runpy

ROOT = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/dieroute')
ORIGINAL = ROOT / 'tools/audit_additional_exhausted_parent.py'
assert hashlib.sha256(ORIGINAL.read_bytes()).hexdigest() == '0c590628351f6c9716031ba323261ffb409f64ef3de586bcd5308763b18a298a'
os.chdir(ROOT)
runpy.run_path(str(ORIGINAL), run_name='__main__')
