#!/usr/bin/env python3
"""Replay native corridor journals as a verifier; never perform route search."""
import argparse
from collections import defaultdict
from contextlib import ExitStack
import csv
import json
import mmap
import shutil
from pathlib import Path
import struct
import time
from run_native_case import sha256
from audit_native_boundary_shadow import journal_hash
from audit_native_schedule import verify_schedule
from audit_native_workers import WorkerAudit

NONE = 0xffffffff


def rows(directory, name):
    with (directory/name).open() as f:
        return [{k: int(v) for k, v in row.items()} for row in csv.DictReader(f)]


def grouped(data, fields):
    out = defaultdict(list)
    for row in data: out[tuple(row[k] for k in fields)].append(row)
    return out


def verify_trace(run, manifest):
    command = manifest['command']; assert len(command) in (14, 15, 16, 17, 18, 19, 20, 21) and int(command[13]) > 0
    joint = int(command[17]) if len(command) >= 18 else 0
    assert joint in (0, 1)
    defer_budget = int(command[18]) if len(command) >= 19 else 0
    assert defer_budget in (0, 1) and (not defer_budget or joint)
    repeat_count = int(command[11]); shadow = int(command[12]); route = run/'route'
    workers=WorkerAudit(route,command)
    calls = rows(route, 'corridor_runs.csv'); stages = rows(route, 'corridor_trace.csv')
    paths = grouped(rows(route, 'corridor_paths.csv'), ('repeat', 'search', 'replay'))
    candidates = grouped(rows(route, 'corridor_candidates.csv'), ('repeat', 'search', 'replay', 'attempt'))
    plans = grouped(stages, ('repeat', 'search', 'replay', 'attempt'))
    journals = grouped(rows(route, 'shadow_reads.csv'), ('repeat', 'search'))
    shadow_trace = {(r['repeat'], r['search']): r for r in rows(route, 'shadow_trace.csv')}
    final_shadows = rows(route, 'shadow_final.csv'); shadow_metrics = rows(route, 'shadow_metrics.csv')
    assert list(shadow_trace) == sorted(shadow_trace)
    selection = {r['task']: r for r in rows(route, 'selection.csv')}
    roots = {}; loads = defaultdict(set)
    for r in selection.values():
        assert r['net'] not in roots or roots[r['net']] == r['source']
        roots[r['net']] = r['source']; loads[r['net']].add(r['sink'])
    iteration_rows = rows(route, 'iterations.csv'); final_trees = rows(route, 'trees.csv'); final_uses = rows(route, 'usage.csv')
    has_schedule = (route/'cohort_passes.csv').exists()
    assert has_schedule or not defer_budget
    pass_records = rows(route, 'cohort_passes.csv') if has_schedule else []
    snapshots = {}; epoch_initial = {}
    key_fields = ('repeat', 'search', 'replay')
    keys = [tuple(r[k] for k in key_fields) for r in calls]
    assert keys == sorted(set(keys))
    total_completed = total_selected = better_entries = better_portals = 0
    candidate_limit = int(command[16]) if len(command) >= 17 else 1
    assert candidate_limit > 0 and (not joint or candidate_limit == 1)
    with ExitStack() as stack:
        def mapped(path):
            f = stack.enter_context(Path(path).open('rb'))
            return stack.enter_context(mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ))
        graph, search, footprint, mapping = map(Path, command[1:5])
        nodes = mapped(graph/'nodes.bin'); pips = mapped(graph/'pips.bin')
        offsets = mapped(search/'offsets.bin'); arcs = mapped(search/'arcs.bin')
        protected = mapped(search/'node_protection.bin'); exclusive = mapped(search/'exclusive_net.bin')
        native_tasks = mapped(footprint/'tasks.bin'); owners = mapped(footprint/'owners.bin'); node_map = mapped(mapping/'footprint_node_map.bin')
        node_count = len(nodes)//64; frozen = bytearray((node_count+7)//8)
        topology_dies = max(memoryview(nodes)[20::64]).bit_length()
        for old, net in struct.iter_unpack('<II', owners):
            if net not in roots:
                n = struct.unpack_from('<I', node_map, old*4)[0]; frozen[n//8] |= 1 << (n % 8)
        def member(n):
            assert 0 <= n < node_count
            return struct.unpack_from('<I', nodes, n*64+20)[0]
        def available(n, net):
            return 0 <= n < node_count and not protected[64+n] and not frozen[n//8] & (1 << (n % 8)) and struct.unpack_from('<I', exclusive, 64+n*4)[0] in (NONE, net)
        def arc_ok(src, dst, key):
            pip = struct.unpack_from('<8I', pips, (key >> 1)*32)
            assert pip[0] == key >> 1 and (pip[7] & 2 or key & 1 == pip[7] & 1)
            assert tuple(pip[1:3][::-1] if key & 1 else pip[1:3]) == (src, dst)
            lo = struct.unpack_from('<Q', offsets, 64+src*8)[0]; end = struct.unpack_from('<Q', offsets, 64+(src+1)*8)[0]; hi = end
            while lo < hi:
                mid = (lo+hi)//2
                if struct.unpack_from('<II', arcs, 64+mid*8) < (dst, key): lo = mid+1
                else: hi = mid
            assert lo < end and struct.unpack_from('<II', arcs, 64+lo*8) == (dst, key)
            return pip[6]
        for rep in range(repeat_count):
            trees = {net: {src: (NONE, NONE, 0)} for net, src in roots.items()}
            uses = {}
            for net, src in roots.items():
                assert src not in uses and available(src, net)
                uses[src] = [set([net]), 0, 1]
            def now(n):
                value = uses.get(n, (set(), 0, 0)); return len(value[0]), value[1], value[2]
            published = {}; publication_count = changed_count = 0
            def publish():
                nonlocal published, publication_count, changed_count
                new = {n: now(n) for n in uses if member(n) & (member(n)-1)}
                assert set(published) <= set(new)
                changed_count += sum(v != published.get(n, (0, 0, 0)) for n, v in new.items())
                publication_count += 1; published = new
            iterations = [r for r in iteration_rows if r['repeat'] == rep]
            assert [r['iteration'] for r in iterations] == list(range(len(iterations)))
            rep_calls = [r for r in calls if r['repeat'] == rep]
            searches = grouped(rep_calls, ('search',))
            assert sorted(k[0] for k in searches) == list(range(len(searches)))
            pending = set(roots)
            for epoch, iteration in enumerate(iterations):
                assert iteration['pending_nets'] == len(pending) and iteration['present'] == 1 << epoch
                if epoch:
                    for value in uses.values():
                        if len(value[0]) > 1: value[1] += len(value[0])-1; value[2] += 1
                    for net in pending:
                        for n in trees[net]:
                            if n != roots[net]: uses[n][0].remove(net); uses[n][2] += 1
                        trees[net] = {roots[net]: (NONE, NONE, 0)}
                epoch_calls = [r for r in rep_calls if r['iteration'] == epoch]
                if has_schedule:
                    for net in pending: epoch_initial[rep, epoch, net] = (len(trees[net]), frozenset(loads[net].intersection(trees[net])))
                for _, attempts in grouped(epoch_calls, ('search',)).items():
                    task = attempts[0]['task']; assert task in selection
                    net = selection[task]['net']; sink = selection[task]['sink']; assert net in pending
                    native_task = struct.unpack_from('<8I', native_tasks, task*32); observer, sink_die = native_task[4:6]
                    search_key = rep, attempts[0]['search']; read_rows = journals.pop(search_key, [])
                    before_search = (len(trees[net]), frozenset(loads[net].intersection(trees[net])))
                    if shadow and search_key[1] % shadow == 0: publish()
                    reads = {r['node']: r for r in read_rows}; assert len(reads) == len(read_rows)
                    stale = False
                    for n, r in reads.items():
                        assert (r['current_occupancy'], r['current_history'], r['current_version']) == now(n)
                        mask = member(n); assert mask & (mask-1) and mask & -mask != 1 << observer
                        old = (r['observed_occupancy'], r['observed_history'], r['observed_version'])
                        assert old == published.get(n, (0, 0, 0)), 'read differs from last published snapshot'
                        assert old[2] <= now(n)[2] and (old[2] != now(n)[2] or old == now(n))
                        stale |= old != now(n)
                    if shadow:
                        st = shadow_trace.pop(search_key)
                        assert st['task'] == task and st['iteration'] == epoch and st['observer'] == observer
                        assert st['remote_reads'] == len(reads) and st['stale'] == stale
                        assert st['read_hash'] == journal_hash(observer, net, 1 << epoch, read_rows)
                        assert st['initial_status'] == attempts[0]['status'] and st['final_status'] == attempts[-1]['status']
                        assert st['overflow'] == (attempts[0]['status'] == -1)
                        assert st['initial_expanded'] == attempts[0]['expanded'] and st['replay_expanded'] == (attempts[-1]['expanded'] if stale else 0)
                    else: assert not reads and not stale
                    assert [r['replay'] for r in attempts] == ([0, 1] if stale else [0])
                    accepted_path = []
                    for call in attempts:
                        assert call['task'] == task and call['iteration'] == epoch
                        key = tuple(call[k] for k in key_fields)
                        workers.call(key,call,topology_dies,member,now,trees[net],lambda n:available(n,net))
                        use_shadow = shadow and call['replay'] == 0
                        def step_cost(n):
                            mask = member(n)
                            if use_shadow and mask & (mask-1) and mask & -mask != 1 << observer:
                                r = reads[n]; return 1+r['observed_history']+(1 << epoch)*r['observed_occupancy']
                            occupancy, history, version = now(n)
                            return 1+history+(1 << epoch)*occupancy
                        def validate_path(info, path, plan=None):
                            attachment = info['attachment']; assert attachment in trees[net]
                            n = attachment; seen = set(); cost = 0; stage = 0
                            if plan: assert member(n) & (1 << plan[0]['die'])
                            for step, p in enumerate(path):
                                dst = p['destination']; assert p['step'] == step and p['source'] == n
                                assert available(dst, net) and dst not in trees[net] and dst not in seen
                                die = arc_ok(n, dst, p['pip_key'])
                                if plan:
                                    workers.edge(die,dst,member)
                                    assert die == plan[stage]['die'] and member(n) & member(dst) & (1 << die)
                                    mask = member(dst)
                                    if mask & (mask-1): assert dst in (plan[stage]['portal'], sink)
                                    if dst == plan[stage]['portal']: stage += 1
                                seen.add(dst); cost += step_cost(dst); n = dst
                            assert n == sink and info['hops'] == trees[net][attachment][2]+len(path) and info['cost'] == cost
                            if plan: assert stage == len(plan)-1
                            return cost, info['hops'], attachment, tuple(p['destination'] for p in path), tuple(p['pip_key'] for p in path)
                        plan_keys = sorted(k for k in plans if k[:3] == key)
                        assert [k[3] for k in plan_keys] == list(range(len(plan_keys))) and len(plan_keys) <= call['plans'] <= int(command[13])
                        reserved_total = 0; chosen = []; completed = []; completed_portals = []; attempt_work = []; attempt_status = []
                        for pk in plan_keys:
                            plan = plans.pop(pk); first = plan[0]
                            assert [p['stage'] for p in plan] == list(range(len(plan)))
                            dies = [p['die'] for p in plan]; assert len(set(dies)) == len(dies) and dies[-1] == sink_die
                            assert any(member(n) & (1 << dies[0]) for n in trees[net])
                            for p in plan: assert all(p[k] == first[k] for k in ('completed', 'selected', 'failed_stage', 'attachment', 'hops', 'cost'))
                            if 'search_status' in first:
                                for p in plan: assert all(p[k] == first[k] for k in ('search_status','expanded','edge_visits'))
                                assert first['search_status'] in (-1,0,1,2,3,4) and bool(first['completed']) == (first['search_status']==0)
                                attempt_work.append((first['expanded'],first['edge_visits']));attempt_status.append(first['search_status'])
                            portals = [p['portal'] for p in plan[:-1]]; assert plan[-1]['portal'] == NONE
                            discovery_failed = joint and not first['completed']
                            if discovery_failed:
                                assert all(n == NONE for n in portals) and first['failed_stage'] == NONE-1
                                portals = []
                            assert len(set(portals)) == len(portals)
                            for i, n in enumerate(portals):
                                assert available(n, net) and n not in trees[net] and member(n) & (1 << dies[i]) and member(n) & (1 << dies[i+1])
                            reserved = set(portals)
                            if not discovery_failed and member(sink) & (member(sink)-1) and sink not in trees[net]: reserved.add(sink)
                            reserved_total += len(reserved)
                            path = candidates.pop(pk, [])
                            if first['completed']:
                                assert first['failed_stage'] == NONE
                                score = validate_path(first, path, plan); completed.append((score, path, first))
                                if portals: completed_portals.append(portals[-1])
                                total_completed += 1
                                if first['selected']: chosen.append((score, path, len(reserved)))
                            else:
                                assert not path and not first['selected'] and (discovery_failed or first['failed_stage'] < len(plan))
                            workers.plan(pk,first,plan,topology_dies,path,member,trees[net],sink,arc_ok,lambda n:available(n,net),step_cost)
                        assert len(completed_portals) <= candidate_limit and len(set(completed_portals)) == len(completed_portals)
                        if 'joint_expanded' in call:
                            assert call['expanded'] == sum(call[k+'_expanded'] for k in ('joint','local','flat'))
                            assert call['edge_visits'] == sum(call[k+'_edge_visits'] for k in ('joint','local','flat'))
                            assert sum(e for e,v in attempt_work) == call['joint_expanded']+call['local_expanded']
                            assert sum(v for e,v in attempt_work) == call['joint_edge_visits']+call['local_edge_visits']
                            assert call['budget_deferrals'] in (0,1)
                            mode=call['fallback_mode'];assert mode in (0,1,2) and (defer_budget or mode==0)
                            if call['budget_deferrals']:
                                assert mode==1 and 2 in attempt_status and call['status']==2 and not completed and call['flat_searches']==0
                            if mode==2:assert not plan_keys and call['plans']==0 and call['flat_searches']==call['fallbacks']==1 and call['budget_deferrals']==0
                            assert all(call[k]>=0 for k in ('joint_expanded','joint_edge_visits','local_expanded','local_edge_visits','flat_expanded','flat_edge_visits'))
                        if call['status'] != -1: assert call['reserved'] == reserved_total
                        assert call['reserved'] == call['released']+call['retained']
                        path = paths.pop(key, [])
                        if call['status'] == 0:
                            score = validate_path(call, path)
                            if call['flat_searches']:
                                assert call['fallbacks'] == 1 and not completed and not chosen and call['retained'] == 0
                            else:
                                assert len(chosen) == 1 and chosen[0][0] == score == min(x[0] for x in completed)
                                assert path == [{k: v for k, v in p.items() if k != 'attempt'} for p in chosen[0][1]]
                                assert call['retained'] == chosen[0][2]; total_selected += 1
                                improved = len(completed) > 1 and chosen[0][0] < completed[0][0]
                                better_entries += improved and completed[0][2]['portal'] == NONE
                                better_portals += improved and completed[0][2]['portal'] != NONE
                        else: assert not path and call['retained'] == 0
                        if call == attempts[-1]: accepted_path = path
                    last = attempts[-1]
                    if last['status'] == 0:
                        parent = last['attachment']; depth = trees[net][parent][2]
                        for p in accepted_path:
                            n = p['destination']; depth += 1; trees[net][n] = (parent, p['pip_key'], depth); parent = n
                            value = uses.setdefault(n, [set(), 0, 0]); assert net not in value[0]; value[0].add(net); value[2] += 1
                    if has_schedule:
                        assert all(c['pass']==last['pass'] and c['fallback_mode']==last['fallback_mode'] for c in attempts)
                        snapshots[search_key] = dict(call=last, before=before_search, after=(len(trees[net]),frozenset(loads[net].intersection(trees[net]))))
                failed = [r for r in selection.values() if r['sink'] not in trees[r['net']]]
                overused = [v for v in uses.values() if len(v[0]) > 1]
                assert iteration['failed_tasks'] == len(failed) and iteration['routed_tasks'] == len(selection)-len(failed)
                assert iteration['overused_nodes'] == len(overused)
                assert iteration['expanded'] == sum(r['expanded'] for r in epoch_calls) and iteration['edge_visits'] == sum(r['edge_visits'] for r in epoch_calls)
                pending = {r['net'] for r in failed}
                for value in overused: pending.update(value[0])
            expected_trees = [dict(repeat=rep, net=net, node=n, parent=v[0], pip_key=v[1], depth=v[2]) for net in trees for n, v in sorted(trees[net].items())]
            assert {(r['net'], r['node']): r for r in expected_trees} == {(r['net'], r['node']): r for r in final_trees if r['repeat'] == rep}
            expected_uses = [dict(repeat=rep, node=n, net=net, history=v[1], version=v[2]) for n, v in sorted(uses.items()) for net in sorted(v[0]) or [NONE]]
            assert expected_uses == [r for r in final_uses if r['repeat'] == rep]
            if shadow:
                publish()
                assert [dict(repeat=rep, node=n, occupancy=v[0], history=v[1], version=v[2]) for n, v in sorted(published.items())] == [r for r in final_shadows if r['repeat'] == rep]
                metric = shadow_metrics[rep]
                assert metric['publications'] == publication_count and metric['changed_summaries'] == changed_count
                assert metric['logical_deliveries'] == changed_count*(topology_dies-1) and metric['retained_summaries'] == len(published)
    assert not plans and not paths and not candidates and not journals and not shadow_trace
    for dataset in (calls, stages):
        for rep in range(1, repeat_count):
            assert [{k: v for k, v in r.items() if k != 'repeat'} for r in dataset if r['repeat'] == rep] == [{k: v for k, v in r.items() if k != 'repeat'} for r in dataset if r['repeat'] == 0]
    metrics = {k: sum(r[k] for r in calls) for k in ('plans', 'local_searches', 'flat_searches', 'repairs', 'fallbacks', 'reserved', 'released', 'retained', 'overcapacity', 'ranked', 'expanded', 'edge_visits')}
    metrics['cost_prunes'] = sum(r.get('cost_prunes', 0) for r in calls)
    metrics['joint_searches'] = sum(r.get('joint_searches', 0) for r in calls)
    for field in ('budget_deferrals','joint_expanded','joint_edge_visits','local_expanded','local_edge_visits','flat_expanded','flat_edge_visits'):
        metrics[field]=sum(r.get(field,0) for r in calls)
    assert all(0 <= r.get('cost_prunes', 0) <= r['local_searches']+r.get('joint_searches', 0) for r in calls)
    assert all((r['local_searches']==0 and r['ranked']==0 and r.get('joint_searches',0)<=r['plans']) if joint else r.get('joint_searches',0)==0 for r in calls)
    schedule=verify_schedule(command,selection,iteration_rows,pass_records,snapshots,epoch_initial) if has_schedule else dict(controller_schedule_verified=False)
    return dict(workers=workers.finish(),repeats=repeat_count, authority_reconstructed=True, complete_candidate_costs_verified=True,
                completed_candidates=total_completed, selected_corridors=total_selected, better_reentry_candidates=better_entries,
                better_portal_candidates=better_portals,
                metrics=metrics,schedule=schedule)


def main():
    if not __debug__: raise RuntimeError('audit requires assertions')
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('run', 'cohort-audit', 'output'): p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args(); run = a.run.resolve(); out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    source_hashes = {}
    for name in (Path(__file__).name, 'run_native_case.py', 'audit_native_boundary_shadow.py','audit_native_schedule.py','audit_native_workers.py','audit_native_label_transport.py'):
        source = Path(__file__).with_name(name); source_hashes[name] = sha256(source); shutil.copy2(source, out/name)
    manifest = json.loads((run/'manifest.json').read_text()); cohort_path = a.cohort_audit.resolve()/'audit.json'; cohort = json.loads(cohort_path.read_text())
    assert manifest['status'] == 'passed' and manifest['inputs_unchanged'] and cohort['passed'] and cohort['inputs_unchanged']
    assert cohort['inputs'][str(run/'manifest.json')] == sha256(run/'manifest.json')
    inputs = dict(cohort['inputs']); inputs[str(cohort_path)] = sha256(cohort_path)
    for name, digest in manifest['artifacts'].items(): inputs[str(run/name)] = digest
    for path, digest in inputs.items(): assert sha256(path) == digest, path
    result = verify_trace(run, manifest)
    for path, digest in inputs.items(): assert sha256(path) == digest, path
    for name, digest in source_hashes.items(): assert sha256(Path(__file__).with_name(name)) == sha256(out/name) == digest
    result.update(schema='dieroute.native_corridor_audit.v1', passed=True, inputs=inputs, inputs_unchanged=True, finished_ns=time.time_ns(),
                  auditor_sources=source_hashes,
                  board_result=False, native_design_legal=None, scope='Serial native corridor candidates, physical PIP SLRs, complete-cost selection, reservation release and reconstructed authority; not new DCP/STA signoff or hardware results')
    (out/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}))


if __name__ == '__main__': main()
