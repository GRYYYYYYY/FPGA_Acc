"""Execute both frozen full-search cases without stop-first-pass."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
results=[]
for cid in (1,2):
 code=subprocess.run([sys.executable,str(R/'tools/predict_full_ram_swap_full_search_v1.py'),str(cid)],cwd=R).returncode
 receipt=R/f'experiments/full_ram_swap_full_search_v1_2026-10-09/candidate_{cid}/receipt.json'
 results.append(dict(candidate=cid,launcher_exit=code,status=json.loads(receipt.read_text())['status'] if receipt.exists() else 'NO_RECEIPT'))
(R/'experiments/full_ram_swap_full_search_v1_2026-10-09/matrix_receipt.json').write_text(json.dumps(results,indent=2)+'\n');print(results,flush=True)
