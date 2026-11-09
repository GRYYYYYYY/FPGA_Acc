"""Independent tiny XML and branch cases for namespace-aware callback audit."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from stream_native_route_audit import audit as original
from stream_native_route_audit_expat_v1 import audit as previous
from stream_native_route_audit_expat_v2 import audit as candidate

R = Path(__file__).resolve().parents[1]
O = R / 'experiments/native_expat_contract_v2_2026-10-10'
O.mkdir()
xml = '<rr_graph><switches><switch id="0"/></switches><rr_nodes><node id="0" type="SOURCE" capacity="1"/><node id="1" type="SINK" capacity="1"/></rr_nodes><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/></rr_edges></rr_graph>'
route = 'Net 0 (test)\nNode: 0 SOURCE Switch: 0\nNode: 1 SINK Switch: -1\n'
cases = [
    ('plain', xml, route, True),
    ('comments', xml.replace('<rr_edges>', '<!-- ignored --><rr_edges>'), route, True),
    ('duplicate_arc', xml.replace('</rr_edges>', '<edge src_node="0" sink_node="1" switch_id="0"/></rr_edges>'), route, True),
    ('unused_bad_switch', xml.replace('</rr_edges>', '<edge src_node="1" sink_node="0" switch_id="9"/></rr_edges>'), route, True),
    ('namespace', xml.replace('<rr_graph>', '<rr_graph xmlns="urn:fixture">'), route, False),
    ('prefix_namespace', xml.replace('<rr_graph>', '<rr_graph xmlns:p="urn:fixture">').replace('<node ', '<p:node '), route, False),
    ('missing_arc', xml.replace('<edge src_node="0" sink_node="1" switch_id="0"/>', ''), route, False),
    ('missing_switch', xml.replace('<switch id="0"/>', ''), route, False),
    ('duplicate_node', xml.replace('</rr_nodes>', '<node id="1" type="SINK" capacity="1"/></rr_nodes>'), route, False),
    ('wrong_type', xml.replace('type="SINK"', 'type="IPIN"'), route, False),
    ('disabled', xml.replace('capacity="1"', 'capacity="0"'), route, False),
    ('malformed', xml[:-3], route, False),
    ('bad_integer', xml.replace('src_node="0"', 'src_node="bad"'), route, False),
    ('duplicate_net', xml, route + route, False),
    ('node_before_net', xml, route.split('\n', 1)[1], False),
    ('sink_without_source', xml, 'Net 0 (test)\nNode: 1 SINK Switch: -1\n', False),
    ('unparsed_node', xml, route + 'Node: nonsense\n', False),
]
rows = []
for name, graph_text, route_text, expected in cases:
    graph = O / (name + '.xml'); path = O / (name + '.route')
    graph.write_text(graph_text); path.write_text(route_text)
    values = []
    for function in [original, candidate]:
        try:
            values.append(('PASS', function(graph, path)))
        except Exception as error:
            values.append(('REJECT', type(error).__name__))
    assert (values[0][0] == 'PASS') == expected, (name, values)
    assert values[0][0] == values[1][0], (name, values)
    if expected:
        assert values[0][1] == values[1][1]
        assert len(values[1][1]['connections']) == 1
        assert values[1][1]['node_occupancy'] == {'0': 1, '1': 1}
        assert values[1][1]['overflow_units'] == 0
    rows.append(dict(case=name, outcome=values[1][0]))
# Demonstrate the namespace defect in v1 rather than silently broadening acceptance.
assert previous(O / 'namespace.xml', O / 'namespace.route')['overflow_units'] == 0
bindings = closure([Path(__file__), R / 'tools/stream_native_route_audit.py', R / 'tools/stream_native_route_audit_expat_v1.py', R / 'tools/stream_native_route_audit_expat_v2.py'])
out = dict(bindings=bindings, cases=rows, namespace_v1_acceptance_defect_demonstrated=True,
           all_selected_contracts_match_original=True,
           scope='Selected tiny positive and rejection cases; exception types may differ. Not universal XML equivalence, full graph speed, pin legality or workflow proof.')
assert all(sha(k) == h for k,h in bindings.items())
(O / 'verification.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'}, indent=2))
