"""Stream original RR identities and reconstruct the exact additive-RC lattice."""
from array import array
from collections import Counter
from fractions import Fraction
import json
from math import lcm
from pathlib import Path
import sys
import time
import xml.etree.ElementTree as E

sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha


def audit(graph, output):
    graph, output = Path(graph).resolve(), Path(output).resolve()
    assert not output.exists()
    begin = time.perf_counter()
    digest = sha(graph)
    classes, class_ids = [], {}
    node_classes = array('I')
    types, switches, used_pairs = Counter(), {}, set()
    stack = []
    edge_count = zero_capacity = 0
    previous_source = -1
    sources_nondecreasing = True
    for event, element in E.iterparse(graph, events=('start', 'end')):
        if event == 'start':
            stack.append(element)
            continue
        parent = stack[-2].tag if len(stack) > 1 else None
        if element.tag == 'switch' and parent == 'switches':
            sid = int(element.get('id'))
            assert sid not in switches and element.get('type') in ['buffer', 'mux', 'tristate']
            timing = element.find('timing')
            assert timing is not None and Fraction(timing.get('Cinternal', '0')) == 0
            resistance, intrinsic = Fraction(timing.get('R', '0')), Fraction(timing.get('Tdel', '0'))
            assert resistance >= 0 and intrinsic >= 0
            switches[sid] = (resistance, intrinsic)
            stack[-2].remove(element)
            element.clear()
        elif element.tag == 'node' and parent == 'rr_nodes':
            assert int(element.get('id')) == len(node_classes)
            typ = element.get('type')
            assert typ in ['SOURCE', 'SINK', 'IPIN', 'OPIN', 'CHANX', 'CHANY']
            capacity = int(element.get('capacity'))
            assert capacity >= 0
            zero_capacity += capacity == 0
            types[typ] += 1
            timing = element.find('timing')
            assert timing is not None
            key = Fraction(timing.get('R')), Fraction(timing.get('C'))
            assert key[0] >= 0 and key[1] >= 0
            if key not in class_ids:
                class_ids[key] = len(classes)
                classes.append(key)
            node_classes.append(class_ids[key])
            stack[-2].remove(element)
            element.clear()
        elif element.tag == 'edge' and parent == 'rr_edges':
            source, sink, switch = [int(element.get(k)) for k in ['src_node', 'sink_node', 'switch_id']]
            assert 0 <= source < len(node_classes) and 0 <= sink < len(node_classes) and switch in switches
            sources_nondecreasing &= source >= previous_source
            previous_source = source
            used_pairs.add((node_classes[sink], switch))
            edge_count += 1
            stack[-2].remove(element)
            element.clear()
        stack.pop()
    assert node_classes and edge_count and switches
    roots = [r * c / 2 for r, c in classes]
    increments = []
    for cid, sid in sorted(used_pairs):
        resistance, capacitance = classes[cid]
        switch_resistance, switch_intrinsic = switches[sid]
        increments.append(switch_intrinsic + switch_resistance * capacitance + resistance * capacitance / 2)
    scale = 1
    for value in roots + increments:
        scale = lcm(scale, value.denominator)
    root_words = [int(v * scale) for v in roots]
    arc_words = [int(v * scale) for v in increments]
    assert all(Fraction(word, scale) == value for word, value in zip(root_words + arc_words, roots + increments))
    assert sha(graph) == digest
    result = dict(
        bindings={str(graph): digest, str(Path(__file__).resolve()): sha(__file__)},
        original_XML_all_node_and_edge_identities_and_electrical_values_pass=True,
        nodes=len(node_classes), edges=edge_count, node_types=dict(types), zero_capacity_nodes=zero_capacity,
        electrical_classes=len(classes), switches=len(switches), used_destination_class_switch_pairs=len(used_pairs),
        raw_edge_sources_nondecreasing=sources_nondecreasing,
        exact_scale=scale, maximum_root_word=max(root_words), maximum_arc_word=max(arc_words),
        static_span_price_weight=scale // (20 * 10**9),
        raw_simple_path_upper_bound=len(node_classes) * max(arc_words) + max(root_words),
        necessary_backend_word_checks=dict(
            raw_simple_path_below_2pow120=len(node_classes) * max(arc_words) + max(root_words) < 2**120,
            static_span_weight_positive_and_u64=0 < scale // (20 * 10**9) < 2**64,
        ),
        native_node_base_and_dynamic_objective_domain_admitted=False,
        elapsed_seconds=time.perf_counter() - begin,
        scope='Independent full original XML stream and exact rational additive buffered-RC lattice, without quantization or route labels. Checks necessary raw/weight domains only; native base-cost array, dynamic price ceiling, timing identity, query coverage, floor searches and complete physical/event audits remain required. This is not route-tree Elmore/STA equivalence or full model admission.',
    )
    with output.open('x') as f:
        f.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'bindings'}), flush=True)


if __name__ == '__main__':
    audit(sys.argv[1], sys.argv[2])
