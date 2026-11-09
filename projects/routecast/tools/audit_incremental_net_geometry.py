"""Real development moves: independent full endpoint bbox vs sparse updates."""
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from incremental_net_geometry import GeometryState

ROOT = Path(__file__).resolve().parents[1]
def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def rebuild(rows, loc):
    groups = {}
    for r in rows:
        groups.setdefault(r['net_id'], set()).update((r['source'], r['sink']))
    return {net: max(loc[n][0] for n in nodes)-min(loc[n][0] for n in nodes)
            + max(loc[n][1] for n in nodes)-min(loc[n][1] for n in nodes) for net, nodes in groups.items()}

def run():
    start = time.perf_counter()
    protocol = ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
    cases = json.loads(protocol.read_text())['cases']
    out = ROOT/'experiments/incremental_net_geometry_2026-10-07'
    out.mkdir(exist_ok=False)
    bindings = {str(protocol): sha(protocol)}
    cache, results, graph_cost = {}, [], []
    for case in cases:
        oldpath, targetpath = Path(case['old']), Path(case['target'])
        old, target = json.loads(oldpath.read_text()), json.loads(targetpath.read_text())
        graph = Path(old['inputs']['graph']['path'])
        for path in (oldpath, targetpath):
            assert sha(path) == case['inputs'][str(path)]
            bindings[str(path)] = sha(path)
        assert old['graph_sha256'] == target['graph_sha256']
        if str(graph) not in cache:
            t = time.perf_counter(); assert sha(graph) == old['graph_sha256']
            loc = {}
            for _, elem in ET.iterparse(graph, events=('end',)):
                if elem.tag == 'node':
                    location = elem.find('loc')
                    loc[int(elem.attrib['id'])] = (int(location.attrib['xlow']), int(location.attrib['ylow']))
                    elem.clear()
            assert sha(graph) == old['graph_sha256']
            cache[str(graph)] = loc
            bindings[str(graph)] = old['graph_sha256']
            graph_cost.append({'graph': str(graph), 'conversion_and_hash_seconds': time.perf_counter()-t})
        loc = cache[str(graph)]
        t = time.perf_counter(); state = GeometryState(old['connections'], loc); setup = time.perf_counter()-t
        oldrows = {r['connection_id']: r for r in old['connections']}
        newrows = {r['connection_id']: r for r in target['connections']}
        assert len(newrows) == len(target['connections']) and newrows.keys() == oldrows.keys()
        t = time.perf_counter(); changes = [r for cid,r in newrows.items() if r != oldrows[cid]]; diff_cost = time.perf_counter()-t
        before = state.total
        t = time.perf_counter(); trial = state.trial(changes, 0); update_cost = time.perf_counter()-t
        assert state.total == before and state.epoch == 0
        t = time.perf_counter(); full = rebuild(target['connections'], loc); full_cost = time.perf_counter()-t
        state.update(changes, 0)
        assert state.spans == full and state.total == sum(full.values())
        snapshot = (dict(state.rows), dict(state.spans), state.total, state.epoch)
        for rows, epoch in ((changes, 0), ([{'connection_id': max(newrows)+1, 'net_id': 0,'source':0,'sink':0}], 1), ([dict(target['connections'][0], source=max(loc)+1)], 1)):
            try: state.update(rows, epoch)
            except (ValueError, KeyError): pass
            else: raise AssertionError('invalid update accepted')
            assert snapshot == (dict(state.rows), dict(state.spans), state.total, state.epoch)
        results.append({'width':case['width'],'index':case['index'],'connections':len(newrows),'changed_connections':len(changes),'dirty_nets':len(trial['dirty']),'old_hpwl':before,'target_hpwl':state.total,'delta_hpwl':state.total-before,'selected_strict_hpwl_rule':state.total<before,'seconds':{'seed_setup':setup,'endpoint_difference':diff_cost,'sparse_trial':update_cost,'independent_full_rebuild':full_cost},'parity':True,'invalid_updates_atomic':True})
    bindings.update({str(p):sha(p) for p in (Path(__file__), ROOT/'tools/incremental_net_geometry.py')})
    assert all(sha(p)==h for p,h in bindings.items())
    report = {'schema':'routecast.geometry.incremental.v1','cases':results,'graphs':graph_cost,'bindings':bindings,'outer_seconds':time.perf_counter()-start,'policy':'strict aggregate endpoint HPWL decrease; labels not read','scope':'12 existing development moves; endpoint JSON prepared; original graph conversion/hashing included in outer clock; 2D endpoint geometry only, no route/STA/occupancy guarantee, no native label evaluation or net gain claim'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(results),'selected':sum(r['selected_strict_hpwl_rule'] for r in results),'outer_seconds':report['outer_seconds'],'graph_seconds':sum(r['conversion_and_hash_seconds'] for r in graph_cost),'sparse_trial_seconds':sum(r['seconds']['sparse_trial'] for r in results)}))

if __name__ == '__main__': run()
