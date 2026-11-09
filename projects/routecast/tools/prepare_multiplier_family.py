"""Fixed complete 4x4 through 9x9 multiplier readiness cohort; no native labels or QoR selection."""
import json
import shutil
import subprocess
import time
from pathlib import Path
from pre_route_endpoints import sha
from reconstruct_vexriscv_sequential_netlist import logical_lines


def main():
    root=Path(__file__).resolve().parents[1]
    candidates=root/'experiments/prospective_family_candidates_2026-10-06'
    manifest=json.loads((candidates/'manifest.json').read_text())
    assert sha(candidates/'manifest.json')==json.loads((candidates/'receipt.json').read_text())['manifest_sha256']
    tool=json.loads((candidates/'frontend_availability.json').read_text())
    yosys=Path(tool['yosys_path']); abc=yosys.parent.parent/'abc/abc'
    assert sha(yosys)==tool['sha256']
    selected=[f'mult_{width}x{width}.v' for width in range(4,10)]
    records=[next(r for r in manifest['records'] if Path(r['archived_path']).name==name) for name in selected]
    out=root/'experiments/multiplier_family_frontend_2026-10-06';out.mkdir()
    shutil.copyfile(__file__,out/'source.py')
    helper=Path(__file__).with_name('reconstruct_vexriscv_sequential_netlist.py')
    shutil.copyfile(helper,out/'logical_lines_source.py')
    protocol={'inputs':records,'yosys_sha256':sha(yosys),'abc_sha256':sha(abc),
              'manifest_sha256':sha(candidates/'manifest.json'),'source_sha256':sha(__file__),
              'helper_sha256':sha(helper),'selection':'all six frozen multipliers width4 through9; chosen before native routing, one multiplier family',
              'unseen_family_claim':False,'scope':'flattened LUT6 mapping, exact synchronous-state restoration and cut CEC; no QoR evaluation'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results=[]
    for record in records:
        path=root/record['archived_path'];assert sha(path)==record['sha256']
        work=out/path.stem;work.mkdir();shutil.copyfile(path,work/'design.v')
        script='read_verilog design.v; synth -top mult_nxn -flatten; dffunmap; check -assert; write_blif flat.blif'
        def run(stage,command):
            start=time.monotonic()
            with (work/(stage+'.log')).open('w') as log:
                code=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
            assert code==0,stage
            return {'stage':stage,'command':command,'wall_s':time.monotonic()-start,'exit_code':code}
        phases=[run('synth',[str(yosys),'-p',script])]
        flat=list(logical_lines(work/'flat.blif'))
        assert sum(s.startswith('.model ') for s in flat)==1
        assert not any(s.startswith('.subckt ') for s in flat), 'unsupported sequential/hard-block cells'
        inputs=next(s.split()[1:] for s in flat if s.startswith('.inputs '))
        outputs=next(s.split()[1:] for s in flat if s.startswith('.outputs '))
        state=[s for s in flat if s.startswith('.latch ')]
        assert state and all(len(s.split())==6 and s.split()[3]=='re' and s.split()[4]=='clk' for s in state)
        cutinputs=list(dict.fromkeys(inputs+[s.split()[2] for s in state]))
        cutoutputs=list(dict.fromkeys(outputs+[s.split()[1] for s in state]+['clk']))
        body=[s for s in flat if not s.startswith(('.model ','.inputs ','.outputs ','.latch ','.end'))]
        (work/'cut.blif').write_text('\n'.join(['.model cut','.inputs '+' '.join(cutinputs),'.outputs '+' '.join(cutoutputs),*body,'.end'])+'\n')
        phases.append(run('map',[str(abc),'-c','read_blif cut.blif; strash; if -K 6; write_blif mapped_cut.blif']))
        assert (work/'mapped_cut.blif').exists()
        phases.append(run('cec',[str(abc),'-c','cec cut.blif mapped_cut.blif']))
        assert 'Networks are equivalent' in (work/'cec.log').read_text()
        mapped=list(logical_lines(work/'mapped_cut.blif'))
        body=[s for s in mapped if not s.startswith(('.model ','.inputs ','.outputs ','.end'))]
        names=[s.split() for s in body if s.startswith('.names ')]
        assert names and max(len(s)-2 for s in names)<=6
        assert not any(s.startswith(('.latch ','.subckt ')) for s in body)
        drivers=inputs+[s[-1] for s in names]+[s.split()[2] for s in state]
        uses=outputs+[v for s in names for v in s[1:-1]]+[v for s in state for v in (s.split()[1],s.split()[4])]
        assert len(drivers)==len(set(drivers)) and not set(uses)-set(drivers)
        (work/'design.blif').write_text('\n'.join(['.model mult_nxn','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs),*body,*state,'.end'])+'\n')
        final=list(logical_lines(work/'design.blif'))
        assert [s for s in final if s.startswith('.latch ')]==state
        result={'design':path.stem,'phases':phases,'luts':len(names),'state_records':len(state),
                'cut_cec_equivalent':True,'state_exact':True,'single_driver_and_all_uses_driven':True,
                'artifacts':{n:sha(work/n) for n in ('flat.blif','cut.blif','mapped_cut.blif','design.blif','cec.log')}}
        (work/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(json.dumps({k:result[k] for k in ('design','luts','state_records','cut_cec_equivalent')}),flush=True)
    assert sha(yosys)==protocol['yosys_sha256'] and sha(abc)==protocol['abc_sha256'] and sha(helper)==protocol['helper_sha256']
    receipt={'protocol_sha256':sha(out/'protocol.json'),'results':results,'unseen_family_claim':False,
             'scope':protocol['scope'],'native_packing_and_port_accounting_verified':False}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
