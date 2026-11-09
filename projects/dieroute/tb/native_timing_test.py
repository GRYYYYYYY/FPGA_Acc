#!/usr/bin/env python3
"""Adverse fixtures for native report evidence (no Vivado installation needed)."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from audit_native_timing import bus_rows, bus_comparison, checked_delays, collection_identity, number, unescape


def collection(*names):
    return '[get_cells [list '+' '.join('{'+n+'}' for n in names)+']]'


def fixture(src=None, dst=None, position=42, requirement='3.000', actual='1.000',
            slack='2.000', corner='Slow', endpoints=2):
    src = src or collection('src[0]', 'src[1]')
    dst = dst or collection('dst[0]', 'dst[1]')
    summary = ('Id  Position  From  To  Corner  Requirement(ns)  Actual(ns)  Slack(ns)\n'
               '--  --------  ----  --  ------  ---------------  ----------  ---------\n'
               f'1  {position}  {src}\n    {dst}\n    {corner} {requirement} {actual} {slack}\n')
    detail = f'Id: 1\nRequirement: {requirement}ns\nEndpoints: {endpoints}\n'
    if corner == 'NA':
        detail += 'No bus skew paths found.\n'
    return summary, detail


class NativeTimingTest(unittest.TestCase):
    def test_position_and_collection_order(self):
        old = bus_rows(*fixture())
        new = bus_rows(*fixture(src=collection('src[1]', 'src[0]'), position=900))
        self.assertTrue(bus_comparison(old, new)['all_coverage_and_reported_values_equal'])

    def test_wrapping(self):
        old = bus_rows(*fixture())
        src = collection('src[1]', 'src[0]').replace('} {', '} \\\n    {')
        new = bus_rows(*fixture(src=src))
        self.assertTrue(bus_comparison(old, new)['all_coverage_and_reported_values_equal'])

    def test_constraint_mutations_rejected(self):
        old = bus_rows(*fixture())
        for kw in [dict(src=collection('src[0]', 'src[2]')),
                   dict(src=collection('dst[0]', 'dst[1]'), dst=collection('src[0]', 'src[1]')),
                   dict(src=collection('src[0]', 'src[1]', 'src[1]')),
                   dict(requirement='4.000', slack='3.000')]:
            with self.subTest(kw=kw), self.assertRaises(AssertionError):
                bus_comparison(old, bus_rows(*fixture(**kw)))

    def test_other_tcl_keeps_exact_identity(self):
        for text in ['[get_cells -hier *src*]', '[get_cells [list {a\\ b} {c}]]',
                     '[get_cells [list {a}]; exec something]']:
            self.assertEqual(collection_identity(text), ['exact_expression', text])

    def test_single_endpoint_not_a_numeric_pass(self):
        old = bus_rows(*fixture())
        single = bus_rows(*fixture(corner='NA', actual='NA', slack='NA', endpoints=1,
                                  src=collection('one_src'), dst=collection('one_dst')))
        result = bus_comparison(old+single, old+single)
        self.assertEqual((result['evaluated'], result['single_endpoint_no_comparison']), (1, 1))
        with self.assertRaises(AssertionError):
            bus_rows(*fixture(corner='NA', actual='NA', slack='NA', endpoints=2))

    def test_negative_slack_is_a_violation_even_if_unchanged(self):
        rows = bus_rows(*fixture(actual='3.100', slack='-0.100'))
        report = bus_comparison(rows, rows)
        self.assertEqual(report['violations'], 1)
        self.assertEqual(report['minimum_slack_ns'], '-0.100')

    def test_value_change_detected(self):
        before = bus_rows(*fixture())
        after = bus_rows(*fixture(actual='1.100', slack='1.900'))
        self.assertFalse(bus_comparison(before, after)['all_coverage_and_reported_values_equal'])

    def test_malformed_or_missing_report_coverage(self):
        summary, detail = fixture()
        for s, d in [(summary, ''), (summary, detail+detail),
                     (summary, detail.replace('Id: 1', 'Id: 2')),
                     (summary, detail.replace('3.000ns', '4.000ns')),
                     (summary+'garbage\n', detail),
                     (summary.replace('1.000 2.000', '1.000 2.100'), detail)]:
            with self.subTest(summary=s, detail=d), self.assertRaises((AssertionError, KeyError)):
                bus_rows(s, d)

    def test_delay_oracle_rejects_estimates_and_invalid_corners(self):
        props = dict(CLASS='net_delay', ESTIMATED='0', NET='n', FAST_MIN='10',
                     FAST_MAX='20', SLOW_MIN='30', SLOW_MAX='40')
        self.assertEqual(checked_delays(props, 'n')['FAST_MIN'], '10')
        for key, value in [('ESTIMATED', '1'), ('NET', 'other'), ('CLASS', 'pin'),
                           ('FAST_MIN', '-1'), ('FAST_MIN', '21'), ('SLOW_MIN', '41'),
                           ('SLOW_MAX', 'NaN'), ('FAST_MAX', 'Infinity')]:
            bad = copy.copy(props);bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises((AssertionError, ValueError)):
                checked_delays(bad, 'n')

    def test_tsv_escape(self):
        self.assertEqual(unescape(r'a\tb\nc\r\\'), 'a\tb\nc\r\\')
        for bad in ['trailing\\', r'bad\q']:
            with self.assertRaises(ValueError):
                unescape(bad)
        for bad in ['NaN', 'Infinity', '-Infinity']:
            with self.assertRaises(ValueError):
                number(bad)


if __name__ == '__main__':
    unittest.main()
