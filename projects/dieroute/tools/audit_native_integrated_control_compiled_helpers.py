"""Independent read-only audit of integrated physical compile artifacts; no signoff."""
import hashlib
import json
from pathlib import Path
from decimal import Decimal
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'work/native_integrated_control_stages_hw_20261015'
OUT = ROOT / 'work/native_integrated_control_compiled_audit_20261015'

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    protocol = json.loads((P / 'protocol.json').read_text())
    bindings = {str(P / 'protocol.json'): digest(P / 'protocol.json')}
    rows = []
    for item in protocol['components']:
        label, name = item['label'], item['kernel']
        review_path = P / (label + '_compiled_XO_review.json')
        review = json.loads(review_path.read_text())
        for field, path in [('xo_sha256', P / (label + '.xo')),
                            ('source_sha256', P / 'source' / item['source']),
                            ('parent_xo_sha256', item['parent_xo']),
                            ('preprocessed_sha256', review['preprocessed']),
                            ('constraint_sha256', review['constraint'])]:
            assert digest(path) == review[field], (label, field)
            bindings[str(path)] = review[field]
        bindings[str(review_path)] = digest(review_path)
        with ZipFile(P / (label + '.xo')) as z, ZipFile(item['parent_xo']) as old:
            def kernel(archive):
                root = ET.fromstring(archive.read(name + '/kernel.xml'))
                return root if root.tag == 'kernel' else root.find('kernel')
            k, parent = kernel(z), kernel(old)
            for tag in ['ports', 'args']:
                assert [n.attrib for n in k.find(tag)] == [n.attrib for n in parent.find(tag)]
            assert k.get('hwControlProtocol') == parent.get('hwControlProtocol') == 'ap_ctrl_chain'
            assert hashlib.sha256(z.read(name + '/cpu_sources/' + item['source'])).hexdigest() == review['source_sha256']
            reports = [n for n in z.namelist() if n.endswith('/syn/report/csynth.xml')]
            assert len(reports) == 1
            top = ET.fromstring(z.read(reports[0]))
            assert Decimal(top.findtext('.//EstimatedClockPeriod')) <= Decimal('2.43309')
        helper_name = ('native_admission_improves_stage' if label != 'commit'
                       else 'p_anonymous_namespace_phase_start_only')
        helpers = list((P / (label + '_temp')).rglob(helper_name + '_csynth.xml'))
        assert len(helpers) == 1, (label, helpers)
        helper = ET.parse(helpers[0]).getroot()
        assert helper.findtext('UserAssignments/TopModelName') == helper_name
        bindings[str(helpers[0])] = digest(helpers[0])
        latency = helper.find('PerformanceEstimates/SummaryOfOverallLatency')
        if label != 'commit':
            assert latency.findtext('Best-caseLatency') == '2'
            assert latency.findtext('Worst-caseLatency') == '2'
            assert latency.findtext('PipelineInitiationInterval') == '1'
        rows.append(dict(label=label, helper=helper_name,
                         helper_estimated_ns=helper.findtext('.//EstimatedClockPeriod'),
                         helper_latency={n.tag: n.text for n in latency},
                         top_resources=review['resources'],
                         top_estimated_ns=top.findtext('.//EstimatedClockPeriod')))
    result = dict(status='three_actual_hw_XOs_ABI_source_hashes_and_compiled_helpers_verified',
                  components=rows, source_sha256=bindings, adopted=False,
                  physical_timing_pass=False, board_result=False, research_complete=False,
                  limitations=['HLS estimates do not establish routed timing.',
                               'Commit split-start existence does not establish timing improvement.',
                               'Comparison with older physical build also changes queue tie ordering.'])
    OUT.mkdir(exist_ok=True)
    destination = OUT / 'independent_audit.json'
    assert not destination.exists(), 'Preserve prior audit; create a versioned successor.'
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], components=rows), indent=2))

if __name__ == '__main__':
    main()
