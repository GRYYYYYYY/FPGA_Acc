"""Replay local-RC path sums from RR XML, independently of the packed Node ABI."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from audit_rr_experiments import audit

run = Path(sys.argv[1]).resolve()
manifest = json.loads((run/'manifest.json').read_text())
assert manifest['returncode'] == 0 and manifest['inputs_unchanged']
for path, expected in manifest['inputs'].items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
pair_file, = [Path(p) for p in manifest['inputs'] if Path(p).name == 'pair.json']
audit(pair_file)  # Verify the complete frozen source/input/native routing evidence.
pair = json.loads(pair_file.read_text())
with (Path(pair['reference'])/'connections.csv').open() as stream:
    tasks = {int(row['id']):row for row in csv.DictReader(stream)}
paths = {}
with (pair_file.parent/'downstream_bounded_0.paths.csv').open() as stream:
    for row in csv.DictReader(stream):
        paths.setdefault(int(row['task_id']), []).append((int(row['path_index']), int(row['resource_id'])))
arcs_by_task = {}
needed = set()
for task, rows in paths.items():
    rows.sort()
    assert [i for i,n in rows] == list(range(len(rows)))
    chain = [int(tasks[task]['source']), *[n for i,n in rows]]
    assert chain[-1] == int(tasks[task]['sink'])
    arcs_by_task[task] = list(zip(chain,chain[1:]))
    needed.update(arcs_by_task[task])
switches, rc, costs = {}, {}, {}
graph = Path(pair['case'])/'rr_graph.xml'
for _, elem in ET.iterparse(graph,events=('end',)):
    if elem.tag == 'switch':
        timing = elem.find('timing')
        switches[int(elem.attrib['id'])] = (float(timing.attrib.get('Tdel',0)),
            float(timing.attrib.get('R',0)),elem.attrib.get('type','mux') not in ('pass_gate','short'))
        elem.clear()
    elif elem.tag == 'node':
        timing = elem.find('timing')
        rc[int(elem.attrib['id'])] = (float(timing.attrib.get('R',0)),float(timing.attrib.get('C',0)))
        elem.clear()
    elif elem.tag == 'edge':
        key = (int(elem.attrib['src_node']),int(elem.attrib['sink_node']))
        if key in needed:
            delay,resistance,buffered = switches[int(elem.attrib['switch_id'])]
            node_r,node_c = rc[key[1]]
            local = delay + (resistance*node_c+node_r*node_c/2 if buffered else resistance*node_c/2)
            value = round(local*1e12)
            assert 0 <= value <= 65535, 'Selected-edge local delay would saturate'
            costs[key] = min(costs.get(key,value),value)
        elem.clear()
assert costs.keys() == needed, 'Missing XML path edge'
profile = json.loads((run/'profile.json').read_text())
assert {row['task_id'] for row in profile['rows']} == paths.keys()
for row in profile['rows']:
    assert row['local_rc_ps'] == sum(costs[edge] for edge in arcs_by_task[row['task_id']])
report = dict(status='passed',connections=len(paths),unique_path_edges=len(needed),
    graph_sha256=hashlib.sha256(graph.read_bytes()).hexdigest(),
    profile_sha256=hashlib.sha256((run/'profile.json').read_bytes()).hexdigest(),
    scope='Independent RR XML edge/RC replay and frozen routing evidence audit; not causal CPD attribution',
    board_result=False)
(run/'independent_xml_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
