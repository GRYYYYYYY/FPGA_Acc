"""Separate archived routed setup failures by clock and describe displayed paths only."""
import argparse,csv,hashlib,io,json,re
from collections import Counter
from decimal import Decimal
from pathlib import Path


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reports',type=Path);p.add_argument('independent_audit',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();root,proof_path,out=[x.resolve() for x in (a.reports,a.independent_audit,a.output)]
    assert not out.exists()
    manifest_path=root/'manifest.json';manifest=json.loads(manifest_path.read_text())
    proof=json.loads(proof_path.read_text());assert proof['status']=='archived_banked_routed_checkpoint_evidence_audited'
    assert manifest['checkpoint_sha256']==proof['checkpoint_sha256']
    report=root/'reports/timing_summary.rpt';clocks_path=root/'reports/clocks.tsv'
    for path in [report,clocks_path]:assert sha(path)==manifest['report_sha256'][path.name]
    clocks_text=clocks_path.read_text().replace(chr(92)+'t',chr(9))
    clocks={r['name']:float(r['period_ns']) for r in csv.DictReader(io.StringIO(clocks_text),delimiter=chr(9))}
    text=report.read_text();assert text.count('| Intra Clock Table')==text.count('| Inter Clock Table')==1
    section=text.split('| Intra Clock Table',1)[1].split('| Inter Clock Table',1)[0]
    rows=[];tns_values=[]
    for line in section.splitlines():
        t=line.split()
        if len(t)!=13 or t[0] not in clocks:continue
        values=[Decimal(x) for x in t[1:]]
        rows.append(dict(clock=t[0],period_ns=clocks[t[0]],wns_ns=float(values[0]),tns_ns=float(values[1]),
            setup_failing=int(values[2]),setup_total=int(values[3]),whs_ns=float(values[4]),
            hold_failing=int(values[6]),pulse_failing=int(values[10])))
        tns_values.append(values[1])
    assert rows and len({r['clock'] for r in rows})==len(rows)
    global_=proof['design_timing_summary']
    assert sum(r['setup_failing'] for r in rows)==global_['setup_failing']
    assert min(r['wns_ns'] for r in rows)==global_['wns_ns']
    failing={r['clock']:r for r in rows if r['setup_failing']}
    assert set(failing)=={'clk_kernel_00_unbuffered_net','hbm_aclk'}
    paths=[];slack_headers=0
    for block in re.split(r'(?=Slack \((?:VIOLATED|MET)\)\s*:)',text)[1:]:
        slack_headers+=1
        def match(pattern):return re.search(pattern,block,re.M)
        slack=match(r'^Slack \((VIOLATED|MET)\)\s*:\s*([-+\d.]+)ns')
        type_=match(r'^\s*Path Type:\s*(.+)')
        group=match(r'^\s*Path Group:\s*(.+)')
        if not slack or not type_ or not group or not type_[1].startswith('Setup') or float(slack[2])>=0:continue
        source=match(r'^\s*Source:\s*(.+)');destination=match(r'^\s*Destination:\s*(.+)')
        data=match(r'Data Path Delay:\s*([-+\d.]+)ns\s*\(logic\s*([-+\d.]+)ns.*?route\s*([-+\d.]+)ns')
        compensation=match(r'Inter-SLR Compensation:\s*([-+\d.]+)ns')
        assert source and destination and data
        source,destination=source[1].strip(),destination[1].strip()
        def module(name):
            for cu in ['net_commit','search_worker','snapshot_search']:
                if '/ulp/'+cu+'/inst/' in name:return cu
            return 'platform_or_interconnect'
        paths.append(dict(group=group[1].strip(),slack_ns=float(slack[2]),source=source,destination=destination,
            source_module=module(source),destination_module=module(destination),data_delay_ns=float(data[1]),
            logic_delay_ns=float(data[2]),route_delay_ns=float(data[3]),
            route_fraction=float(data[3])/float(data[1]),
            inter_slr_compensation_ns=float(compensation[1]) if compensation else None))
    summaries={}
    for clock,row in failing.items():
        selected=[r for r in paths if r['group']==clock];assert selected
        assert min(r['slack_ns'] for r in selected)==row['wns_ns']
        summaries[clock]=dict(displayed_failing_setup_paths=len(selected),
            source_modules=dict(Counter(r['source_module'] for r in selected)),
            destination_modules=dict(Counter(r['destination_module'] for r in selected)),
            displayed_paths_with_inter_slr_compensation=sum(r['inter_slr_compensation_ns'] is not None for r in selected),
            minimum_displayed_route_fraction=min(r['route_fraction'] for r in selected),
            maximum_displayed_route_fraction=max(r['route_fraction'] for r in selected))
    out.mkdir()
    table=out/'displayed_failing_setup_paths.csv'
    with table.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(paths[0]),lineterminator='\n');writer.writeheader();writer.writerows(paths)
    files=[Path(__file__).resolve(),manifest_path,proof_path,report,clocks_path]
    result=dict(status='archived_setup_failures_separated_by_clock_with_bounded_path_diagnostics',
        checkpoint_sha256=proof['checkpoint_sha256'],xclbin_sha256=proof['xclbin_sha256'],
        intra_clock_rows=rows,failing_clocks=failing,displayed_path_summaries=summaries,
        displayed_failing_setup_paths=len(paths),all_slack_sections_seen=slack_headers,
        setup_failing_endpoints_sum=sum(r['setup_failing'] for r in rows),
        reported_clock_tns_sum_ns=float(sum(tns_values)),reported_global_tns_ns=global_['tns_ns'],
        reported_tns_sum_difference_ns=float(sum(tns_values)-Decimal(str(global_['tns_ns']))),
        source_sha256={str(path):sha(path) for path in files},output_sha256={str(table):sha(table)},
        scope='Archived routed DCP clock-domain setup aggregates cross-check exact failing-endpoint total andworstslack. Detailedpathsaretool-selecteddisplayedexamples,notallfailingendpoint/module distributions. Per-clock TNS sumdiffers0.002nsfromglobalreport;causeunproven. HBMhierarchypath_17doesnotidentifyaHBMpseudochannelbyitself. No finalbitstreamcorrespondence,adjusted187MHzclosure,physicalfrequency/latencyorFmaxclaim.',
        full_signoff_complete=False,board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],failing_clocks=failing,displayed_path_summaries=summaries)))


if __name__=='__main__':main()
