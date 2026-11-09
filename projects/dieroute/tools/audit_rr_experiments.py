#!/usr/bin/env python3
"""Recompute evidence from immutable pair artifacts; manifests alone are insufficient."""
import argparse
import csv
import json
from pathlib import Path
import re
import statistics
import struct
import xml.etree.ElementTree as ET
from run_native_case import sha256
from native_base_costs import verify_export


def verify(path, expected):
    observed = sha256(path)
    if observed != expected:
        raise ValueError(f"hash mismatch: {path}")


def verify_lookahead_work(actual, configuration, executed_env):
    """Extra local searches must be included in the reported total work."""
    if 'cost_scale' in configuration:
        scale = configuration['cost_scale']
        if type(scale) is not int or scale not in (1,256) or actual.get('cost_scale') != scale:
            raise ValueError('cost precision configuration/output mismatch')
        if executed_env is None or executed_env.get('DIEROUTE_COST_SCALE') != str(scale):
            raise ValueError('executed cost precision setting mismatch')
    if 'upstream_cost' not in configuration:
        return  # Retain compatibility with frozen pre-variant measurements.
    enabled = configuration['upstream_cost']
    if not isinstance(enabled, bool) or actual.get('upstream_cost') is not enabled:
        raise ValueError('upstream configuration/output mismatch')
    if executed_env is None or executed_env.get('DIEROUTE_UPSTREAM_COST') != str(int(enabled)):
        raise ValueError('missing or mismatched executed upstream setting')
    for suffix, total in (('expanded', 'expanded'), ('edge_visits', 'edge_visits')):
        upstream = actual.get('upstream_' + suffix)
        downstream = actual.get('downstream_' + suffix)
        if any(type(value) is not int or value < 0 for value in (upstream, downstream, actual.get(total))):
            raise ValueError('invalid lookahead work counter')
        if upstream + downstream > actual[total]:
            raise ValueError('lookahead work omitted from total')
        if not enabled and upstream:
            raise ValueError('disabled upstream mode reports work')
    searches = actual.get('upstream_searches')
    if type(searches) is not int or searches < 0 or (not enabled and searches):
        raise ValueError('invalid upstream search counter')
    if 'bound_upstream' in configuration:
        bounded = configuration['bound_upstream']
        if type(bounded) is not bool or actual.get('bound_upstream') is not bounded:
            raise ValueError('upstream stop configuration/output mismatch')
        if executed_env.get('DIEROUTE_BOUND_UPSTREAM') != str(int(bounded)):
            raise ValueError('executed upstream stop setting mismatch')
        cutoffs = actual.get('upstream_cutoffs')
        if type(cutoffs) is not int or not 0 <= cutoffs <= searches or (not bounded and cutoffs):
            raise ValueError('invalid upstream stop counter')


def native_crossings(route, owners):
    crossings = set()
    net, previous = None, None
    for line in route.read_text().splitlines():
        match = re.match(r"^\s*Net\s+(\d+)\s+", line)
        if match:
            net, previous = int(match[1]), None
            continue
        match = re.match(r"^\s*Node:\s*(\d+)\s+.*\bSwitch:\s*(-?\d+)", line)
        if not match:
            continue
        node, switch = int(match[1]), int(match[2])
        if net is None or node >= len(owners): raise ValueError("invalid native route node/net")
        if previous is not None and owners[previous] != owners[node]:
            crossings.add((net, previous, node))
        # A leaf ends the traceback. The next printed node is a branch anchor,
        # not an edge from this leaf to the anchor.
        previous = None if switch == -1 else node
    return {"net_crossing_edges": len(crossings),
            "net_crossing_destinations": len({(net, b) for net, a, b in crossings})}


def verify_task_order(base, mode, repeat, manifest, actual, executed_env):
    if 'task_order' not in manifest['configuration']:
        return
    declared = manifest['configuration']['task_order']
    assert declared in ('preserve','local_distance') and actual.get('task_order') == declared
    assert executed_env.get('DIEROUTE_LOCAL_TASK_ORDER') == str(int(declared == 'local_distance'))
    task_input = base/'input.tasks' if 'native_cost_export' in manifest else Path(manifest['reference'])/'input.tasks'
    tasks = list(struct.iter_unpack('<IIIIHHIII',task_input.read_bytes()))
    owners = [r[0] for r in struct.iter_unpack('<H',(base/'topology.node_die').read_bytes())]
    boxes = list(struct.iter_unpack('<HHHH',(base/'topology.node_box').read_bytes()))
    expected = {}
    groups = {}
    for t in tasks:
        ident,net,source,sink,_,_,priority,_,_ = t
        a,b = boxes[source],boxes[sink]
        gap = max(0,a[0]-b[2],b[0]-a[2]) + max(0,a[1]-b[3],b[1]-a[3])
        expected[ident] = dict(task_id=ident,net_id=net,old_priority=priority,new_priority=priority,
                               remote=int(owners[source] != owners[sink]),gap=gap)
        groups.setdefault(net,[]).append(ident)
    assert len(expected) == len(tasks)
    if declared == 'local_distance':
        assert len({t[6] for t in tasks}) == len(tasks)
        for ids in groups.values():
            pool = sorted(expected[i]['old_priority'] for i in ids)
            ordered = sorted(ids,key=lambda i:(expected[i]['remote'],expected[i]['gap'],i))
            for i,priority in zip(ordered,pool):expected[i]['new_priority'] = priority
    with (base/f'{mode}_{repeat}.task_order.csv').open() as stream:
        rows = [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    assert len(rows) == len(tasks) and {r['task_id'] for r in rows} == expected.keys()
    assert all(row == expected[row['task_id']] for row in rows), 'Incorrect declared task permutation'


def verify_cleanup(base,mode,repeat,manifest,actual,env):
    config = manifest['configuration']
    if 'cleanup_passes' not in config:return
    for field in ('cleanup_passes','cleanup_length_cost_q','cleanup_delay_tolerance_ppm','cleanup_per_connection_guard'):
        assert actual[field] == config[field],field
    assert env.get('DIEROUTE_CLEANUP_PASSES') == str(config['cleanup_passes'])
    active = bool(config['cleanup_passes'] and actual['legal'])
    assert actual['final_audit_stage'] == ('cleanup' if active else 'routing')
    with (base/f'{mode}_{repeat}.cleanup.csv').open() as stream:
        rows = [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    if not active:
        assert not rows and actual['cleanup_accepted_nets'] == 0
        return
    with (base/f'{mode}_{repeat}.audit.csv').open() as stream:
        audits = list(csv.DictReader(stream))
    assert len(audits) == actual['iterations'] + 1, 'Missing explicit post-cleanup terminal audit'
    assert int(audits[-1]['iteration']) == actual['iterations']
    previous = int(audits[-2]['resource_hash'])
    accepted = delta = 0
    for row in rows:
        assert row['pass'] < config['cleanup_passes']
        assert all(row[k] in (0,1) for k in ('complete','delay_ok','feasible','accepted'))
        assert row['before_hash'] == previous, 'Broken cleanup authority chain'
        expected = bool(row['complete'] and row['delay_ok'] and row['feasible'] and row['candidate_wire'] < row['old_wire'])
        assert bool(row['accepted']) == expected
        if row['accepted']:
            accepted += 1;delta += row['old_wire']-row['candidate_wire']
        else:assert row['before_hash'] == row['after_hash'], 'Rejected cleanup failed authority rollback'
        previous = row['after_hash']
    assert previous == int(audits[-1]['resource_hash'])
    assert accepted == actual['cleanup_accepted_nets'] <= actual['cleanup_attempted_nets']
    assert actual['cleanup_wirelength_before']-actual['cleanup_wirelength_after'] == delta
    task_input = base/'input.nodes' if 'native_cost_export' in manifest else Path(manifest['reference'])/'input.nodes'
    spans = [n[2] for n in struct.iter_unpack('<IHH',task_input.read_bytes())]
    by_net = {}
    with (base/f'{mode}_{repeat}.route_trees.csv').open() as stream:
        for row in csv.DictReader(stream):by_net.setdefault(int(row['net_id']),set()).update((int(row['source']),int(row['parent']),int(row['child'])))
    assert sum(spans[n] for nodes in by_net.values() for n in nodes) == actual['cleanup_wirelength_after']


def verify_channel_span_prices(base,mode,repeat,manifest,actual,env):
    if 'channel_span_price_q' not in manifest['configuration']:
        return
    price=manifest['configuration']['channel_span_price_q']
    if type(price) is not int or price not in (0,64) or actual.get('channel_span_price_q')!=price:
        raise ValueError('channel span price configuration differs')
    if env is None or env.get('DIEROUTE_CHANNEL_SPAN_PRICE_Q')!=str(price):
        raise ValueError('channel span price environment differs')
    if price and (actual.get('edge_identity') or manifest['configuration']['cleanup_passes']):
        raise ValueError('unsupported span price mode')
    prefix=base/'input' if 'native_cost_export' in manifest else Path(manifest['reference'])/'input'
    nodes=list(struct.iter_unpack('<IHH',Path(str(prefix)+'.nodes').read_bytes()))
    original=list(struct.iter_unpack('<IHH',Path(str(prefix)+'.edges').read_bytes()))
    effective=list(struct.iter_unpack('<IHH',(base/f'{mode}_{repeat}.effective.edges').read_bytes()))
    if len(original)!=len(effective):
        raise ValueError('effective edge count changed')
    spans={}
    for _,node in ET.iterparse(Path(manifest['case'])/'rr_graph.xml',events=('end',)):
        if node.tag=='node':
            span=0
            if node.attrib['type'] in ('CHANX','CHANY'):
                axis='x' if node.attrib['type']=='CHANX' else 'y';loc=node.find('loc')
                span=int(loc.attrib[axis+'high'])-int(loc.attrib[axis+'low'])+1
            spans[int(node.attrib['id'])]=span;node.clear()
    if len(nodes)!=len(spans) or any(row[2]!=spans.get(i) for i,row in enumerate(nodes)):
        raise ValueError('packed span differs from native geometry')
    for old,new in zip(original,effective):
        dst,base_price,delay=old
        expected=base_price+price*max(0,spans[dst]-1)
        if expected>65535 or new!=(dst,expected,delay):
            raise ValueError('effective edges changed topology/delay or span price')


def audit(path):
    d = json.loads(path.read_text())
    if d["status"] != "completed":
        raise ValueError(f"measurement is not complete: {path}")
    base = path.parent
    for rel, expected in d["source_sha256"].items():
        verify(base / rel, expected)
    verify(base / "build/dieroute_rr", d["binary_sha256"])
    case, reference = Path(d["case"]), Path(d["reference"])
    verify(case / "run.json", d["native_run_sha256"])
    verify(reference / "reference.json", d["reference_sha256"])
    if "timing_vpr" in d:
        verify(Path(d["timing_vpr"]["path"]), d["timing_vpr"]["sha256"])
    native = json.loads((case / "run.json").read_text())
    for rel, meta in native["artifacts"].items():
        verify(case / rel, meta["sha256"])
    pr = json.loads((reference / "reference.json").read_text())
    for rel, meta in pr["artifacts"].items():
        verify(reference / rel, meta["sha256"])
    if "native_cost_export" in d:
        cost_dir = Path(d["native_cost_export"]["path"])
        verify(cost_dir / "costs.json", d["native_cost_export"]["sha256"])
        verify_export(cost_dir, case)
        verify(base / "input.costs.json", d["rebased_input_sha256"])
        rebased = json.loads((base / "input.costs.json").read_text())
        if rebased['cost_export_sha256'] != d['native_cost_export']['sha256']:
            raise ValueError('rebased inputs use another cost export')
        for ext, expected in rebased['artifacts'].items():
            verify(base / ('input.' + ext), expected)
        for ext in ('nodes', 'resources', 'tasks'):
            verify(base / ('input.' + ext), sha256(reference / ('input.' + ext)))
        costs = [x[0] for x in struct.iter_unpack('<H', (cost_dir / 'node_base_cost').read_bytes())]
        before, after = [(root / 'input.edges').read_bytes() for root in (reference, base)]
        if len(before) != len(after):
            raise ValueError('rebased graph edge count changed')
        for old, new in zip(struct.iter_unpack('<IHH', before), struct.iter_unpack('<IHH', after)):
            if new != (old[0], costs[old[0]], old[2]):
                raise ValueError('rebase changed topology/delay or has wrong destination cost')
    for step in d["steps"]:
        verify(base / (step["label"] + ".log"), step["log_sha256"])
    topology = json.loads((base / "topology.topology.json").read_text())
    verify(case / "rr_graph.xml", topology["rr_graph_sha256"])
    for artifact, meta in topology["artifacts"].items():
        verify(Path(artifact), meta["sha256"])
    owners = [n[0] for n in struct.iter_unpack("<H", (base / "topology.node_die").read_bytes())]
    result = {"manifest": str(path), "manifest_sha256": sha256(path),
              "configuration": d["configuration"], "case": str(case),
              "topology": {k: topology[k] for k in ("node_count", "die_count", "tasks")},
              "verified_source_files": len(d["source_sha256"]), "modes": {}}
    result["native_model_crossings"] = native_crossings(case / "circuit.route", owners)
    for mode, data in d["modes"].items():
        if len(data["runs"]) < 5 or len(data["hashes"]) != len(data["runs"]):
            raise ValueError("fewer than five complete repeats")
        for i, hashes in enumerate(data["hashes"]):
            for ext, expected in hashes.items():
                verify(base / f"{mode}_{i}.{ext}", expected)
            actual = json.loads((base / f"{mode}_{i}.json").read_text())
            routing_steps = [step for step in d['steps'] if step['label'] == f'{mode}_{i}']
            if len(routing_steps) != 1:
                raise ValueError('missing or duplicate routing step')
            executed_env = routing_steps[0].get('routing_environment')
            verify_lookahead_work(actual, d['configuration'], executed_env)
            verify_task_order(base, mode, i, d, actual, executed_env)
            verify_cleanup(base, mode, i, d, actual, executed_env)
            verify_channel_span_prices(base, mode, i, d, actual, executed_env)
            if executed_env is not None:
                if executed_env.get('DIEROUTE_GEOMETRY_WEIGHT') != str(d['configuration']['geometry_weight']):
                    raise ValueError('executed geometry weight differs from configuration')
            if actual != data["runs"][i]:
                raise ValueError("copied metrics differ from raw output")
            if "route_tree_timing_weight_q" in d["configuration"]:
                if actual.get("route_tree_timing_weight_q") != d["configuration"]["route_tree_timing_weight_q"]:
                    raise ValueError("executed route-tree timing weight differs from configuration")
            for setting in ('cost_model', 'criticality_cap_q', 'cost_state_bits', 'speculative_workers', 'shadow_sync_windows', 'upstream_cost', 'cost_scale'):
                if setting in d['configuration'] and actual.get(setting) != d['configuration'][setting]:
                    raise ValueError('executed cost model differs from configuration')
        if any(h != data["hashes"][0] for h in data["hashes"]):
            raise ValueError("repeat semantic outputs differ")
        counters = [{k: v for k, v in r.items() if k != "wall_ms"} for r in data["runs"]]
        if any(c != counters[0] for c in counters):
            raise ValueError("repeat semantic counters differ")
        entry = {"status": data["status"], "repeats_verified": len(counters),
                 "deterministic_outputs_and_counters": True, "counters": counters[0],
                 "median_cpu_wall_ms": statistics.median(r["wall_ms"] for r in data["runs"])}
        if "speculative_workers" in d["configuration"]:
            with (base / f"{mode}_0.transactions.csv").open() as stream:
                trace = list(csv.DictReader(stream))
            active = d["configuration"]["speculative_workers"] > 0
            if counters[0]["execution"] != ("cpu_speculative_reference" if active else "serial_cpp_reference"):
                raise ValueError("executed backend differs from declared workers")
            if not active and trace:
                raise ValueError("serial backend emitted speculative transactions")
            if active:
                stale = sum(row["initial_status"] == "stale" for row in trace)
                if (stale != counters[0]["speculative_conflicts"] or stale != counters[0]["speculative_replays"]
                        or len(trace) + stale != counters[0]["speculative_proposals"]):
                    raise ValueError("transaction trace disagrees with speculation counters")
                last = None
                for row in trace:
                    order = tuple(int(row[k]) for k in ("window", "epoch", "priority", "task_id"))
                    if last is not None and order <= last:
                        raise ValueError("transaction commit order is not a fixed total order")
                    last = order
                    if row["final_status"] not in ("committed", "unreachable", "capacity"):
                        raise ValueError("unresolved transaction in accepted experiment")
                    if row["initial_status"] not in ("committed", "unreachable", "capacity", "stale") or row["replayed"] not in ("0", "1"):
                        raise ValueError("unknown transaction state/replay flag")
                    if (row["replayed"] == "1") != (row["initial_status"] == "stale"):
                        raise ValueError("replay journal missing or unexpected")
                    if row["replayed"] == "0" and (row["initial_status"] != row["final_status"] or
                            row["initial_reads"] != row["final_reads"] or int(row["replay_read_hash"]) != 0):
                        raise ValueError("unchanged proposal has inconsistent commit/journal metadata")
                read_entries = sum(int(row["initial_reads"]) + (int(row["final_reads"]) if row["replayed"] == "1" else 0)
                                   for row in trace)
                windows = {}
                for row in trace:
                    window = int(row["window"])
                    windows[window] = windows.get(window, 0) + 1
                if read_entries != counters[0]["speculative_read_entries"]:
                    raise ValueError("read journal counts disagree with transaction trace")
                if (sorted(windows) != list(range(counters[0]["speculative_windows"])) or
                        max(windows.values(), default=0) != counters[0]["maximum_window_tasks"] or
                        max(windows.values(), default=0) > counters[0]["speculative_workers"]):
                    raise ValueError("speculative window size/count mismatch")
                if counters[0]["shadow_summary_payload_bytes"] != 32 * counters[0]["shadow_messages"]:
                    raise ValueError("shadow payload counter inconsistent with declared 32-byte messages")
            entry["transaction_trace_verified"] = True
        with (base / f'{mode}_0.iterations.csv').open() as stream:
            iteration_rows = list(csv.DictReader(stream))
        saturated_iterations = [int(row['iteration']) for row in iteration_rows
                                if int(row['present_factor_q']) == 65535]
        states = list(struct.iter_unpack('<HHHHII', (base / f'{mode}_0.resources').read_bytes()))
        saturated_resources = sum(state[2] == 65535 or state[3] == 65535 for state in states)
        bits = counters[0].get('cost_state_bits', 16)
        if 'cost_state_bits' in d['configuration']:
            costs = list(struct.iter_unpack('<QQ', (base / f'{mode}_0.costs').read_bytes()))
            if len(costs) != len(states) or len(costs) != topology['node_count']:
                raise ValueError('authoritative cost/resource count mismatch')
            if counters[0]['cost_encoding'] != 'little_endian_u64_present_history':
                raise ValueError('unknown cost encoding')
            if (max(c[0] for c in costs), max(c[1] for c in costs)) != (
                    counters[0]['maximum_present_q'], counters[0]['maximum_history_q']):
                raise ValueError('maximum cost counters differ from binary state')
            if bits == 64:
                if counters[0]['resource_encoding'] != 'pr16_zero_cost_fields_plus_cost64_v1' or any(s[2] or s[3] for s in states):
                    raise ValueError('wide resources have ambiguous narrow cost fields')
                for i, row in enumerate(iteration_rows):
                    if int(row['iteration']) != i or int(row['present_factor_q']) != 256 << i:
                        raise ValueError('wide factor differs from frozen Q8 growth schedule')
                if any(c[0] != int(iteration_rows[-1]['present_factor_q']) for c in costs):
                    raise ValueError('final authoritative factors differ from iteration log')
                saturated_iterations, saturated_resources = [], 0
            elif bits == 16:
                if counters[0]['resource_encoding'] != 'pr16_v1' or any(c != (s[2], s[3]) for c, s in zip(costs, states)):
                    raise ValueError('legacy cost sidecar differs from PR state')
            else:
                raise ValueError('unknown cost width')
            # Match the C++ logical resource hash, including authoritative wide
            # costs rather than zero/reserved fields in the compatibility blob.
            resource_hash = 1469598103934665603
            for state, cost in zip(states, costs):
                for word in (state[0], state[1], cost[0], cost[1], state[4], state[5]):
                    for byte in word.to_bytes(8, 'little'):
                        resource_hash = ((resource_hash ^ byte) * 1099511628211) & ((1 << 64) - 1)
            with (base / f'{mode}_0.audit.csv').open() as stream:
                final_audit = list(csv.DictReader(stream))[-1]
            if resource_hash != int(final_audit['resource_hash']):
                raise ValueError('authoritative final resource hash differs from controller audit')
            entry['authoritative_costs_verified'] = True
            entry['cost_state_bits'] = bits
        entry['fixed_point_valid'] = not saturated_iterations and not saturated_resources
        entry['fixed_point_saturation'] = {'present_iterations': saturated_iterations,
                                            'final_saturated_resources': saturated_resources}
        entry['quality_evidence_eligible'] = entry['fixed_point_valid'] and data['status'] == 'passed'
        if data["status"] != "passed":
            result["modes"][mode] = entry
            continue
        validation = base / (mode + "_validation")
        v = json.loads((validation / "validation.json").read_text())
        if v != data["native_validation"] or not v["legal"] or v["vpr_exit_status"] != 0:
            raise ValueError("native validation missing or inconsistent")
        verify(validation / "vpr_analysis.stdout", v["stdout_sha256"])
        verify(validation / "vpr_analysis.stderr", v["stderr_sha256"])
        verify(base / (mode + ".route"), v["inputs"]["route_sha256"])
        verify(case / "circuit.place", v["inputs"]["place_sha256"])
        text = (validation / "vpr_analysis.stdout").read_text()
        for marker in ("Finished loading route file", "Completed routing consistency check successfully.",
                       "Circuit successfully routed", "VPR succeeded"):
            if marker not in text: raise ValueError(f"missing native check marker: {marker}")
        wl = int(re.findall(r"Total wirelength:\s+(\d+)", text)[-1])
        cpd = float(re.findall(r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns", text)[-1])
        if (wl, cpd) != (v["total_wirelength"], v["critical_path_delay_ns"]):
            raise ValueError("native raw QoR differs from summary")
        entry["native_qor"] = {k: v[k] for k in ("total_wirelength", "critical_path_delay_ns", "baseline_wirelength",
            "baseline_cpd_ns", "wirelength_delta_percent", "cpd_delta_percent")}
        crossings = set()
        with (base / f"{mode}_0.route_trees.csv").open() as stream:
            for row in csv.DictReader(stream):
                net, a, b = (int(row[k]) for k in ("net_id", "parent", "child"))
                if owners[a] != owners[b]: crossings.add((net, a, b))
        entry["final_net_crossing_edges"] = len(crossings)
        entry["final_net_crossing_destinations"] = len({(net, b) for net, a, b in crossings})
        result["modes"][mode] = entry
    if {"downstream", "downstream_bounded"} <= d["modes"].keys():
        # Read-set traces legitimately differ between full and bounded searches;
        # paths, resources, costs and controller audit must still be identical.
        full = {k: v for k, v in d["modes"]["downstream"]["hashes"][0].items() if k != "transactions.csv"}
        bounded = {k: v for k, v in d["modes"]["downstream_bounded"]["hashes"][0].items() if k != "transactions.csv"}
        result["bounded_preserves_full_semantic_outputs"] = full == bounded
        if not result["bounded_preserves_full_semantic_outputs"]:
            raise ValueError("bounded lookahead changes routed outputs")
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("manifests", nargs="+", type=Path)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    report = {"schema": "dieroute.audited_rr_experiments.v1", "board_result": False,
              "research_complete": False, "experiments": [audit(path.resolve()) for path in args.manifests]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "verified_experiments": len(report["experiments"])}))
