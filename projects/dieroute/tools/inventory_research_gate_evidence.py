"""Inventory declared gate evidence; file existence never proves a research gate."""
import argparse
import hashlib
import json
from pathlib import Path


def inventory(root, plan_path):
    plan = json.loads(plan_path.read_text())
    gates = []
    for gate in plan['gates']:
        references = []
        for field, value in gate.items():
            if not isinstance(value, str) or not value.startswith(('work/', 'experiments/', 'paper/', 'tools/')):
                continue
            path = root / value
            record = dict(field=field, path=value, exists=path.is_file())
            if path.is_file():
                data = path.read_bytes()
                record.update(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                if path.suffix == '.json':
                    try:
                        evidence = json.loads(data)
                        if isinstance(evidence, dict):
                            record['reported_status'] = evidence.get('status')
                            record['reported_board_result'] = evidence.get('board_result')
                            record['reported_research_complete'] = evidence.get('research_complete')
                    except (ValueError, UnicodeDecodeError) as error:
                        record['parse_error'] = str(error)
            references.append(record)
        gates.append(dict(id=gate['id'], requirement=gate['requirement'],
                          declared_status=gate['status'],
                          verified_complete=False,
                          reason='Requirement-wide validation is still required; this inventory checks declared references only.',
                          remaining=gate.get('remaining'), evidence=references))
    return dict(schema='dieroute.research_gate_evidence_inventory.v1',
                plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                scope='Declared direct reference inventory, not transitive evidence validation or a completion audit',
                research_complete=False, gates=gates,
                missing_references=[r['path'] for g in gates for r in g['evidence'] if not r['exists']],
                malformed_json=[r['path'] for g in gates for r in g['evidence'] if 'parse_error' in r])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    report = inventory(root, root / 'experiments/research_plan.json')
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(gates=len(report['gates']), missing=report['missing_references'],
                         malformed=report['malformed_json'], research_complete=False)))
