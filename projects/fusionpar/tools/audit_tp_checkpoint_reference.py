#!/usr/bin/env python3
"""Check that selected/visited native TP placements retain the shared contract."""
import argparse
import json
from pathlib import Path

from audit_development import require
from prepare_vpr_bundle import endpoints, tp, sha


def checked(entry):
    p=Path(entry['path'])
    require(sha(p)==entry['sha256'],'changed checkpoint artifact: '+str(p))
    return p


def audit(path):
    reference=json.loads(path.read_text());rows=[]
    for design,data in reference['designs'].items():
        initial=data['population'][0]
        contract=Path(initial['artifacts']['net']['path']).parent.parent/'inputs/contract'
        expected_net=initial['artifacts']['net']['sha256']
        for row in data['population']:
            if not row['legal']:continue
            artifacts={k:checked(v) for k,v in row['artifacts'].items()}
            require(row['artifacts']['net']['sha256']==expected_net,'checkpoint changed packed design')
            result=tp.validate_contract(contract,artifacts['place'])
            require(result['legal'],'native canonical placement violates shared contract')
            if row['trial']:
                closure=json.loads(checked(row['closure']).read_text())
                golden=checked(closure['inputs']['golden_place'])
                # Frozen run_vpr_closure validates the canonical VPR output
                # after routing. Its certificate hashes that serialization,
                # not the original proposal (whose header/format may differ).
                require(closure['placement_validation']['placement_sha256']==row['artifacts']['place']['sha256'],
                        'native placement certificate is bound to another canonical output')
                require(endpoints.placements(golden,expected_net)==endpoints.placements(artifacts['place'],expected_net),
                        'native routing changed proposed placement coordinates/identity')
            rows.append({'design':design,'trial':row['trial'],'selected':row['trial']==data['selected']['trial'],
                         'placement_sha256':row['artifacts']['place']['sha256'],'contract_check':result})
    require(len(rows)==75 and sum(r['selected'] for r in rows)==3,'incomplete checkpoint contract population')
    return {'schema':'FUSIONPAR_TP_CHECKPOINT_CONTRACT_AUDIT_V1','pass':True,
            'reference':{'path':str(path),'sha256':sha(path)},'auditor_sha256':sha(__file__),
            'helper_sources':[{'path':str(Path(p).resolve()),'sha256':sha(p)} for p in (tp.__file__,endpoints.__file__)],
            'rows':rows,'limits':['Additional placement/identity audit; no new TP search or runtime benchmark']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('reference',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():p.error('output already exists')
    result=audit(a.reference.resolve());a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'pass':True,'canonical_placement_checks':len(result['rows']),'selected_checks':sum(r['selected'] for r in result['rows'])}))
