"""Authenticate local generation lineage; no assertion of upstream or unseen identity."""
import json
import re
import shutil
from pathlib import Path
from pre_route_endpoints import sha


def main():
    root=Path(__file__).resolve().parents[1]
    candidates=root/'experiments/prospective_family_candidates_2026-10-06'
    manifest=json.loads((candidates/'manifest.json').read_text())
    assert sha(candidates/'manifest.json')==json.loads((candidates/'receipt.json').read_text())['manifest_sha256']
    vtr=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
    path=vtr/'vtr_flow/benchmarks/arithmetic/adder_trees/verilog'
    template=path/'adder_tree.v';generator=path/'duplicate_adder_trees.bash'
    before={str(p):sha(p) for p in (template,generator)}
    raw=template.read_bytes()
    out=root/'experiments/adder_tree_family_lineage_2026-10-06';out.mkdir()
    shutil.copyfile(template,out/'template.v');shutil.copyfile(generator,out/'generator.bash');shutil.copyfile(__file__,out/'source.py')
    records=[]
    for row in manifest['records']:
        match=re.fullmatch(r'adder_tree_([23])L_(\d{3})bits.v',Path(row['archived_path']).name)
        if not match:continue
        level,width=match.groups();archived=root/row['archived_path']
        assert sha(archived)==row['sha256']
        regenerated=raw.replace(b'%%LEVELS_OF_ADDER%%',level.encode()).replace(b'%%ADDER_BITS%%',width.encode())
        assert regenerated==archived.read_bytes(), row['archived_path']
        records.append({'path':row['archived_path'],'sha256':row['sha256'],'depth':int(level),'width':int(width),'template_regeneration_byte_exact':True})
    assert len(records)==54
    assert all(sha(p)==h for p,h in before.items())
    result={'inputs':before,'candidate_manifest_sha256':sha(candidates/'manifest.json'),'source_sha256':sha(__file__),
            'variants':records,'all_54_variants_regenerate_byte_exact':True,
            'family_policy':'all depths and widths derive from one template and belong to one family; never split sibling variants between development and holdout',
            'upstream_commit_authenticated':False,'unseen_family_claim':False,
            'limitations':['local generator identity does not authenticate upstream revision','prior indirect related-family exposure remains unproven','current four-case results are readiness/transfer evidence only']}
    (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('all_54_variants_regenerate_byte_exact','upstream_commit_authenticated','unseen_family_claim')}))


if __name__=='__main__':main()
