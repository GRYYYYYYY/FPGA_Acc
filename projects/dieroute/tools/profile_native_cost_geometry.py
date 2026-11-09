"""Profile static channel prices versus spans; do not alter routing objectives."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET
from native_base_costs import verify_export
from profile_rr_wirelength_regression import routed_nodes

root = Path(__file__).resolve().parents[1]
audit = json.loads((root/'experiments/wide_timing_cohort_audit_20261013.json').read_text())
reports = []
for experiment in audit['experiments']:
    case = Path(experiment['case'])
    name = case.name.split('_')[1]
    directory = root / f'work/native_costs_{name}_20261013'
    verify_export(directory,case)
    prices = [row[0] for row in struct.iter_unpack('<H',(directory/'node_base_cost').read_bytes())]
    spans, groups = {}, Counter()
    for _,node in ET.iterparse(case/'rr_graph.xml',events=('end',)):
        if node.tag == 'node':
            ident = int(node.attrib['id'])
            if node.attrib['type'] in ('CHANX','CHANY'):
                loc = node.find('loc');axis = 'x' if node.attrib['type'] == 'CHANX' else 'y'
                span = int(loc.attrib[axis+'high'])-int(loc.attrib[axis+'low'])+1
                spans[ident] = span
                groups[(span,prices[ident])] += 1
            node.clear()
    candidate = Path(experiment['manifest']).parent/'downstream_bounded.route'
    before,after = [routed_nodes(path) for path in (case/'circuit.route',candidate)]
    assert before.keys() == after.keys()
    def total(routes, values):
        return sum(values[n] for ns in routes.values() for n in ns if n in spans)
    bw,cw = total(before,spans),total(after,spans)
    expected = experiment['modes']['downstream_bounded']['native_qor']
    assert bw == expected['baseline_wirelength'] and cw == expected['total_wirelength']
    bp,cp = total(before,prices),total(after,prices)
    files = [case/'rr_graph.xml',case/'circuit.route',candidate,directory/'node_base_cost',directory/'costs.json']
    reports.append(dict(case=name,baseline_wirelength=bw,candidate_wirelength=cw,
        baseline_static_channel_price=bp,candidate_static_channel_price=cp,
        static_price_delta_percent=100*(cp/bp-1),
        span_price_groups=[dict(span=s,price=p,nodes=count) for (s,p),count in sorted(groups.items())],
        source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files}))
report = dict(status='measured',cases=reports,
    scope='Static unique-channel price per net versus actual geometric span; excludes dynamic congestion and criticality',
    interpretation='Segment prices are shared by different clipped spans, but all3 candidate routes also increase total static channel price. A geometry-price mismatch alone is not demonstrated as the cause of wirelength regression.',
    board_result=False,research_complete=False)
path = root/'work/native_cost_geometry_profile_20261014.json'
path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status=report['status'],output=str(path))))
