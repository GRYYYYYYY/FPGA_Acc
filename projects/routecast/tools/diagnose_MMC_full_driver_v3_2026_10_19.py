"""Bounded first16 end-to-end driver reproduction, including serialization."""
import pathlib,faulthandler
r=pathlib.Path(__file__).resolve().parents[1]
log=(r/'experiments/mmc_full_driver_diagnosis_v3_stack.log').open('x');faulthandler.dump_traceback_later(15,repeat=True,file=log)
p=r/'tools/run_MMC_full_NET_tree_ensemble_v1_2026_10_19.py';s=p.read_text().replace('mmc_full_NET_tree_ensemble_v1_2026-10-19','mmc_full_driver_diagnosis_v3_2026-10-19').replace("cases=[f'episode_{i:02d}' for i in range(1,4)]","cases=['episode_01']").replace('enumerate(sorted(groups.items()),1)','enumerate(sorted(groups.items())[:16],1)').replace('assert len(index)==55300','assert len(index)==16')
s=s.replace("    sources={q['source'] for q in qs};", "    print('DRIVER NET START',net,flush=True)\n    sources={q['source'] for q in qs};")
s=s.replace("     record=dict(","     print('DRIVER SERIALIZE',net,flush=True)\n     record=dict(")
exec(compile(s,str(p), 'exec'),{'__file__':str(p),'__name__':'__main__'})
faulthandler.cancel_dump_traceback_later()
