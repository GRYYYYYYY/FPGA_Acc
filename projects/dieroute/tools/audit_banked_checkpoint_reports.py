"""Audit preserved independent banked DCP reports without asserting image finality or signoff."""
import argparse,hashlib,json,math,re
from collections import Counter
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reports',type=Path);p.add_argument('build',type=Path);p.add_argument('clock_audit',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    root,build,clock_path,out=[x.resolve() for x in (a.reports,a.build,a.clock_audit,a.output)];out.mkdir(exist_ok=False)
    manifest=root/'manifest.json';m=json.loads(manifest.read_text());assert m['status']=='archived_checkpoint_reports_require_finality_and_signoff_audit' and m['returncode']==0
    assert all(sha(root/'reports'/name)==digest for name,digest in m['report_sha256'].items());assert sha(m['checkpoint'])==m['checkpoint_sha256']
    b=json.loads((build/'manifest.json').read_text());assert b['status']=='linked_requires_independent_routed_signoff' and b['inputs_unchanged']
    clock=json.loads(clock_path.read_text());groups_path=build/'group_audit/audit.json';groups=json.loads(groups_path.read_text());assert clock['xclbin_sha256']==groups['xclbin_sha256']==b['xclbin_sha256']
    report_dir=root/'reports';timing=(report_dir/'timing_summary.rpt').read_text()
    pattern=r'WNS\(ns\).*?\n\s*-+[^\n]*\n\s*([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)\s+([-\d.]+)\s+([-\d.]+)\s+(\d+)\s+(\d+)'
    match=re.search(pattern,timing,re.S);assert match;v=match.groups()
    summary=dict(wns_ns=float(v[0]),tns_ns=float(v[1]),setup_failing=int(v[2]),setup_total=int(v[3]),whs_ns=float(v[4]),ths_ns=float(v[5]),hold_failing=int(v[6]),hold_total=int(v[7]),wpws_ns=float(v[8]),tpws_ns=float(v[9]),pulse_failing=int(v[10]),pulse_total=int(v[11]))
    def table(name):
        lines=(report_dir/name).read_text().splitlines();assert lines
        # Preserve source bytes; this archived Tcl emitted literal backslash-t separators.
        separator='\\t' if '\\t' in lines[0] else '\t';return [line.split(separator) for line in lines if line]
    metrics=dict(table('metrics.tsv'));assert metrics['part']=='xcu280-fsvh2892-2L-e'
    assert int(metrics['setup_path_count'])==int(metrics['hold_path_count'])==1
    assert float(metrics['setup_worst_slack_ns'])==summary['wns_ns'] and float(metrics['hold_worst_slack_ns'])==summary['whs_ns']
    utilization=(report_dir/'utilization.rpt').read_text();resources={}
    for label,key in [('CLB LUTs','lut'),('CLB Registers','ff'),('Block RAM Tile','bram_tiles'),('URAM','uram'),('DSPs','dsp')]:
        match=re.search(r'^\|\s*'+re.escape(label)+r'\s*\|\s*([\d.]+)\s*\|',utilization,re.M);assert match;resources[key]=float(match[1])
    drc=(report_dir/'drc.rpt').read_text();declared=int(re.search(r'Violations found:\s+(\d+)',drc)[1]);rules=[];severity=Counter()
    for rule,level,count in re.findall(r'^\|\s*([A-Z][A-Z0-9-]+)\s*\|\s*(Critical Warning|Warning|Advisory|Error)\s*\|[^|\n]*\|\s*(\d+)\s*\|',drc,re.M):
        rules.append(dict(rule=rule,severity=level,count=int(count)));severity[level]+=int(count)
    assert sum(severity.values())==declared
    route=(report_dir/'route_status.rpt').read_text();route_counts={}
    for label,key in [('logical nets','logical'),('routable nets','routable'),('fully routed nets','fully_routed'),('nets with routing errors','routing_errors')]:
        match=re.search(r'# of '+label+r'\.+\s*:\s*(\d+)',route);assert match;route_counts[key]=int(match[1])
    coverage={};check=(report_dir/'check_timing.rpt').read_text()
    for key in ['no_clock','unconstrained_internal_endpoints','no_input_delay','no_output_delay']:
        match=re.search(r'checking '+key+r' \((\d+)\)',check);assert match;coverage[key]=int(match[1])
    clocks=table('clocks.tsv');assert clocks[0]==['name','period_ns']
    clock_rows=[dict(name=r[0],period_ns=float(r[1])) for r in clocks[1:]];assert all(math.isfinite(r['period_ns']) and r['period_ns']>0 for r in clock_rows)
    kernel=table('kernel_clocks.tsv');assert kernel[0]==['kernel','cell','pin','clock','period_ns']
    paths=[manifest,build/'manifest.json',groups_path,clock_path,Path(__file__).resolve(),*[report_dir/name for name in m['report_sha256']]]
    result=dict(status='archived_banked_routed_checkpoint_evidence_audited',checkpoint_sha256=m['checkpoint_sha256'],xclbin_sha256=b['xclbin_sha256'],design_timing_summary=summary,resources=resources,drc_declared_violations=declared,drc_severity_counts=dict(severity),drc_rules=rules,route_counts=route_counts,constraint_counts=coverage,clock_rows=clock_rows,kernel_clock_rows=kernel[1:],kernel_clock_mapping_complete=bool(kernel[1:]),clock_metadata=dict(requested_mhz=clock['requested_mhz'],tool_reported_achieved_mhz=clock['tool_reported_achieved_mhz'],data_clock_topology_mhz=clock['data_clock_topology_mhz']),setup_pass=summary['setup_failing']==0 and summary['wns_ns']>=0,hold_pass=summary['hold_failing']==0 and summary['whs_ns']>=0,pulse_pass=summary['pulse_failing']==0 and summary['wpws_ns']>=0,route_complete=route_counts['routable']==route_counts['fully_routed'] and route_counts['routing_errors']==0,drc_error_or_critical_warning_count=severity['Error']+severity['Critical Warning'],drc_warning_waivers_proven=False,final_bitstream_correspondence_proven=False,full_signoff_complete=False,source_sha256={str(p):sha(p) for p in paths},scope='Independent read-only preserved routed checkpoint reports;hashes and scalar cross-checks. Default DRC warnings/advisories are not waived by this audit. Empty per-CU clock probe,IO constraint coverage and final-bitstream correspondence remain open. Original300MHz setup fails;image187MHz metadata is not adjusted-clock signoff,Fmax orboard execution.',board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','design_timing_summary','resources','drc_severity_counts','route_complete','kernel_clock_mapping_complete','full_signoff_complete']}))
if __name__=='__main__':main()
