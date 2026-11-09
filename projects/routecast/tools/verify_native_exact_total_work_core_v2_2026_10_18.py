import sys,json,struct,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from parse_native_work_exact_totals_v2_2026_10_18 import parse
D=R/'experiments/native_exact_total_work_core_v2_2026-10-18';D.mkdir();helper=R/'tools/native_wire_work_independent_v2.py';source=helper.read_text();prefix=source[source.index('def audit('):source.index(' unions={}',source.index('def audit('))];namespace=dict(Path=Path,struct=struct);exec(prefix+' return table\n',namespace);independent=namespace['audit'];rows=[];bindings={str(p):sha(p) for p in [Path(__file__).resolve(),helper,R/'tools/parse_native_work_exact_totals_v2_2026_10_18.py']}
for case in ['case_01','case_02','case_03']:
 for arm in ['off','on']:
  log=R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18'/case/arm/'native.log';text=log.read_text();a=parse(text);b=independent(log,None,None,None);assert len(a['rows'])==len(b)
  for x,y in zip(a['rows'],b):assert all(x[k]==v for k,v in y.items())
  bindings[str(log)]=sha(log);rows.append(dict(case=case,arm=arm,total_heap_pushes=a['total_heap_pushes'],reconstruction=a['exact_heap_reconstruction']))
text=(R/'experiments/mmc_partial_firstpass_native_v1_2026-10-18/case_02/on/native.log').read_text();assert parse(text)['exact_heap_reconstruction'][0]['exact_heap_pushes']==12947363
lines=text.splitlines();row1=next(x for x in lines if x.split()[:1]==['1'] and len(x.split())>9 and x.split()[8].startswith('('));w=row1.split();w[4]='1.0e+07'
fixtures={'two_rounded':text.replace(row1,' '.join(w)),'bad_rounding':text.replace('1.3e+07','1.2e+07'),'missing_total': '\n'.join(x for x in lines if not x.startswith('Router Stats:')),'duplicate_total':text+'\n'+next(x for x in lines if x.startswith('Router Stats:')),'missing_iteration':text.replace(row1,'')}
for name,value in fixtures.items():
 rejected=0
 with tempfile.NamedTemporaryFile(mode='w',suffix='.log') as f:
  f.write(value);f.flush()
  for fn in [lambda:parse(value),lambda:independent(f.name,None,None,None)]:
   try:fn()
   except (AssertionError,ValueError):rejected+=1
  assert rejected==2,name
vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';route=R/'build/native_partial_net_firstpass_v1_2026-10-18/source/route.cpp';util=vendor/'vpr/src/util/vpr_utils.cpp';status=vendor/'vpr/src/route/route_utils.cpp';assert 'router_stats.combine(iter_results.stats);' in route.read_text() and 'total_heap_pushes: %zu' in route.read_text() and 'scientific_precision, float(value)' in util.read_text()
for p in [route,util,status]:bindings[str(p)]=sha(p)
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,all6_both_parsers_every_integer_row_equal=True,rows=rows,negative_fixture_count=len(fixtures),both_parsers_reject_all_negative_fixtures=True,scope='Unique missing heap cell recovered from exact same-run aggregate minus allother exact rows and checked against native float32 two-significant-digit printing. Never round a scientific token to an assumed integer; multiple unknowns rejected. No native rerun.'),f,indent=2)
print('EXACT TOTAL WORK CORE PASS all6 dual-parser equality,5dual rejections',flush=True)
