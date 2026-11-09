"""Extract report evidence; successful parsing is never complete design signoff."""
from collections import Counter
import math
import re


def parse_timing_summary(text):
    match = re.search(r'^\s*WNS\(ns\)[^\n]*\n\s*-+[^\n]*\n\s*([^\n]+)', text, re.M)
    if not match or len(values := match[1].split()) != 12:
        raise ValueError('Missing complete setup/hold/pulse timing summary')
    fields = ['WNS_ns', 'TNS_ns', 'setup_failed', 'setup_total',
              'WHS_ns', 'THS_ns', 'hold_failed', 'hold_total',
              'WPWS_ns', 'TPWS_ns', 'pulse_failed', 'pulse_total']
    result = {}
    for i, (key, value) in enumerate(zip(fields, values)):
        result[key] = int(value) if i % 4 in (2, 3) else float(value)
        if not math.isfinite(result[key]):
            raise ValueError('Nonfinite timing value')
    for name in ['setup', 'hold', 'pulse']:
        if not 0 <= result[name + '_failed'] <= result[name + '_total']:
            raise ValueError('Inconsistent endpoint counts')
    measured_met = (all(result[k] >= 0 for k in ['WNS_ns', 'TNS_ns', 'WHS_ns', 'THS_ns', 'WPWS_ns', 'TPWS_ns'])
                    and all(result[k + '_failed'] == 0 and result[k + '_total'] > 0
                            for k in ['setup', 'hold', 'pulse']))
    markers = re.findall(r'^\s*(?:All user specified )?timing constraints are (not )?met\.\s*$', text, re.M | re.I)
    if len(markers) != 1 or (not bool(markers[0])) != measured_met:
        raise ValueError('Missing or contradictory timing result marker')
    checks = {}
    for name, count in re.findall(r'checking (\w+) \((\d+)\)', text):
        if name in checks and checks[name] != int(count):
            raise ValueError('Contradictory check_timing counts')
        checks[name] = int(count)
    result['check_timing'] = checks
    result['reported_setup_hold_pulse_met'] = measured_met
    result['constraint_coverage_requires_review'] = any(checks.values()) or not checks
    return result


def parse_route_status(text):
    counts = {key.strip(): int(value) for key, value in
              re.findall(r'# of ([a-z ]+)\.+\s*:\s*(\d+)', text)}
    required = ['logical nets', 'nets not needing routing', 'internally routed nets',
                'nets with no loads', 'routable nets', 'fully routed nets',
                'nets with routing errors']
    if any(key not in counts for key in required):
        raise ValueError('Missing route status counts')
    if (counts['logical nets'] != counts['nets not needing routing'] + counts['routable nets']
            or counts['nets not needing routing'] != counts['internally routed nets'] + counts['nets with no loads']):
        raise ValueError('Inconsistent route status totals')
    return {'counts': counts, 'reported_routing_complete':
            counts['routable nets'] > 0 and counts['fully routed nets'] == counts['routable nets']
            and counts['nets with routing errors'] == 0}


def parse_violation_report(text):
    match = re.search(r'Violations found:\s*(\d+)', text)
    if not match:
        raise ValueError('Missing declared violation count')
    total, rules, severity = int(match[1]), {}, Counter()
    for line in text.splitlines():
        parts = [v.strip() for v in line.split('|')]
        if len(parts) != 6 or not parts[4].isdigit():
            continue
        rule, level, count = parts[1], parts[2], int(parts[4])
        if level not in ['Error', 'Critical Warning', 'Warning', 'Advisory', 'Info'] or rule in rules:
            raise ValueError('Unknown severity or duplicate rule')
        rules[rule] = {'severity': level, 'count': count}
        severity[level] += count
    if sum(severity.values()) != total:
        raise ValueError('Violation summary count mismatch')
    return {'total': total, 'severity': dict(severity), 'rules': rules}


def crosscheck_drc_properties(summary, text):
    rows = {}
    lines = text.splitlines()
    if not lines or lines[0] != 'violation\tproperty\tvalue':
        raise ValueError('Missing DRC property table header')
    for line in lines[1:]:
        name, prop, value = line.split('\t', 2)
        if prop in rows.setdefault(name, {}):
            raise ValueError('Duplicate violation property')
        rows[name][prop] = value
    if len(rows) != summary['total']:
        raise ValueError('DRC detail count mismatch')
    if Counter(row['SEVERITY'] for row in rows.values()) != Counter(summary['severity']):
        raise ValueError('DRC severity/detail mismatch')
    if Counter(row['CHECK'] for row in rows.values()) != Counter({k: v['count'] for k, v in summary['rules'].items()}):
        raise ValueError('DRC rule/detail mismatch')
    waived = 0
    for row in rows.values():
        value = row['IS_WAIVED'].lower()
        if value not in ['0', '1', 'false', 'true']:
            raise ValueError('Unknown waiver state')
        waived += value in ['1', 'true']
    return {'details_checked': len(rows), 'waived_count': waived}
