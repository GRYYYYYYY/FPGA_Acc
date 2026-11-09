"""Replay frozen baseline selector body against versioned input-only selector output."""
import ast,json,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
R=Path(__file__).resolve().parents[1];P=R/'experiments/xtea_seed_selection_order_v1_2026-10-09';rp=P/'receipt.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());epfile=next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json'));sp=next(Path(p) for p in r['bindings'] if p.endswith('/sketch.json'));ep=json.loads(epfile.read_text());c=json.loads(sp.read_text());xml=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);source=R/'tools/select_resident_native_seed_subset_v1.py';tree=ast.parse(source.read_text());outer=next(n for n in tree.body if isinstance(n,ast.For));start=next(i for i,n in enumerate(outer.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');stop=next(i for i,n in enumerate(outer.body) if i>start and isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='w' for t in n.targets));scope=dict(c=c,ep=ep,xml=xml,groups=defaultdict(list),Counter=Counter)
exec(compile(ast.Module(body=outer.body[start:stop],type_ignores=[]),str(source),'exec'),scope)
f=P/'connection_count.json';a=json.loads(f.read_text());row=next(x for x in r['rows'] if x['policy']=='connection_count');assert sha(f)==row['output_sha256']
for k in ['records','pending','decisions']:assert a[k]==scope[k],k
assert {int(k):v for k,v in a['ledger'].items()}==dict(scope['ledger'])
D=R/'experiments/xtea_selection_baseline_parity_v1_2026-10-09';D.mkdir(exist_ok=True);bindings={**closure([Path(__file__)]),str(source):sha(source),str(rp):sha(rp),str(f):sha(f),str(epfile):sha(epfile),str(sp):sha(sp)}
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,frozen_original_baseline_records_pending_decisions_ledger_equal=True,connections=len(a['records']),pending=len(a['pending']),scope='Original baseline Python AST selection body executed on complete XTEA development input; full output field parity. Not native routing, alternate-policy optimality, heldout or performance proof.'),indent=2)+'\n');print('PASS original selection baseline full field parity')
