"""All width endpoints from packed placement and RR only, retaining mapping errors."""
import hashlib,json,time,traceback
from pathlib import Path
from pre_route_endpoints import extract
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_prospective_endpoints_v1_2026-10-09';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases={128:E/'full_ram_route_predictor_off_v1_2026-10-09',
    192:E/'full_ram_width_matrix_v1_2026-10-09/cw192',256:E/'full_ram_width_matrix_v1_2026-10-09/cw256'}
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/pre_route_endpoints.py']}
for folder in cases.values():
    for name in ('design.net','design.place','rr_graph.xml'):bindings[str(folder/name)]=sha(folder/name)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,widths=list(cases),clock_policy='exclude_root_clocks',
    scope='Complete endpoint extraction from .net/.place/RR XML only, no route reads. Family development candidate, not unseen-family status. Fail unsupported physical mapping rather than fallback to target routes.'),indent=2)+'\n')
results=[]
for width,folder in cases.items():
    out=D/f'cw{width}';out.mkdir();t=time.perf_counter()
    try:
        endpoints,report=extract(folder/'design.net',folder/'design.place',folder/'rr_graph.xml')
        (out/'endpoints.json').write_text(json.dumps(endpoints,indent=2)+'\n')
        (out/'mapping.json').write_text(json.dumps(report,indent=2)+'\n')
        result=dict(width=width,passed=True,connections=len(endpoints['connections']),external_nets=report['external_nets'],seconds=time.perf_counter()-t)
    except Exception as error:
        (out/'error.txt').write_text(traceback.format_exc())
        result=dict(width=width,passed=False,error=repr(error),seconds=time.perf_counter()-t)
    results.append(result);(D/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print(result,flush=True)
assert all(sha(Path(p))==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,admitted_as_unseen_family=False,
    files={str(p):sha(p) for p in D.rglob('*') if p.is_file()}),indent=2)+'\n')
