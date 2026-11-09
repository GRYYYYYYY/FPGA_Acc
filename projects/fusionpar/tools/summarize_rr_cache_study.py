#!/usr/bin/env python3
"""Compact, hash-bound summary of export-cache equivalence and full costs."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
from statistics import median

from audit_development import require
from run_development import ROOT, sha


def binding(path):
    return {'path':str(Path(path).resolve()),'sha256':sha(path)}


def summarize(path):
    study=json.loads(path.read_text());counts=defaultdict(int);designs={};pairs=0
    for design,data in study['designs'].items():
        require(data['pass'],'failed equivalence study')
        for entry in data['evidence']:
            require(sha(entry['path'])==entry['sha256'],'changed cache study evidence')
        for a in data['audits'].values():
            require(a['pass'],'failed publication audit')
            for key,value in a['counts'].items():counts[key]+=value
        pairs+=len(data['byte_equivalent_validations'])
        modes={}
        for mode,values in data['modes'].items():
            modes[mode]={k:values[k] for k in ('quality','samples','medians')}
            modes[mode]['median_RR_export_metadata_seconds']={
                backend:median(row[backend]['phase_seconds'][phase] for row in values['samples'])
                for backend,phase in (('xml','rr_graph_decode'),('sqlite','rr_metadata_lookup'))}
        designs[design]={'modes':modes,'full_preparation_seconds':data['full_preparation_seconds'],
            'cache_construction_and_roundtrip_seconds':data['cache_construction_and_roundtrip_seconds'],
            'cache_bytes':data['cache_bytes'],
            'node_count':data['cache_metadata']['node_count'],
            'edge_pair_count':data['cache_metadata']['edge_pair_count'],
            'ambiguous_pair_count':data['cache_metadata']['ambiguous_pair_count']}
    require(counts['runs']==60 and pairs==90,'incomplete paired population')
    negative=ROOT/'work/rr_cache_negative_v1/checks.json'
    checks=json.loads(negative.read_text());require(checks['pass'] and len(checks['cases'])==5,'missing negative controls')
    return {'schema':'FUSIONPAR_RR_EXPORT_CACHE_RESULTS_V1','study':binding(path),
            'summarizer':binding(__file__),'pilot':binding(ROOT/'work/ex5p_rr_cache_pilot_v1/pilot.json'),
            'negative_controls':binding(negative),'counts':dict(counts),'paired_native_validations':pairs,
            'byte_equality_checks':pairs*7,'designs':designs,'limits':study['limits']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('study',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    result=summarize(a.study.resolve());a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'counts':result['counts'],'paired_native_validations':result['paired_native_validations'],
                      'byte_equality_checks':result['byte_equality_checks']},indent=2))
