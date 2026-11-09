"""Verify all logged sink states and save/restore parity; distinguish clustered delay from atom timing increment."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_best_state_audit_2026-10-07'
r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(f)==h for f,h in p['bindings'].items())
rows=[];terminal={}
for q in r['rows']:
 assert all(sha(f)==h for f,h in q['files'].items())
 d=[x for x in q['events'] if x[0]=='RC_BEST_DELAY'];assert d and all(x[-2]==x[-1] for x in d)
 states={}
 for x in d:states.setdefault((x[1],int(x[2])),{})[(x[3],x[5])]=(x[4],x[-2],x[-1])
 save=[k for k in states if k[0]=='save'];assert len(save)==1
 it=save[0][1];assert states[save[0]]==states[('restored',it)]==states[('pruned',it)]
 counts=Counter(x[1] for x in d)
 rows.append(dict(width=q['width'],mode=q['mode'],logged_delay_rows=len(d),stages=dict(counts),save_iteration=it,matrix_tree_mismatches=0,save_restore_prune_equal=True))
 if q['width']==16:
  terminal[q['mode']]=[x for x in d if x[1]=='pruned' and x[4]=='y6_9']
assert terminal['workflow'][0][-2:]==terminal['cold'][0][-2:]
a=physical_paths(out/'w16_m1_workflow/output.route')['y6_9'];b=physical_paths(out/'w16_m1_cold/output.route')['y6_9'];assert Counter(a)==Counter(b)
up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src'
sources={str(up/f):sha(up/f) for f in ('timing/PostClusterDelayCalculator.tpp','base/vpr_api.cpp')}
result=dict(rows=rows,terminal_y6_9_final_same_delay_and_physical_paths=True,terminal_states=terminal,read_only_sources=sources,receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),scope='All logged sinks in four controls only; one save per run so no earlier-best restoration exercised. Atom timing increment includes launch/capture cluster delays; final analysis reloads net delays and constructs a new timing analyzer.')
(out/'state_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
