import json,re,hashlib
from pathlib import Path
from audit_native_route import NET,NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_seed_fanout_ablation_2026-10-06';work=root/'work/native_seed_fanout_ablation_2026-10-06'
# Reuse independently reconstructed per-pin physical path comparison, without executing its trial-specific checks.
s=(root/'tools/verify_native_search_seed.py').read_text();ns={'re':re,'NET':NET,'NODE':NODE};exec(s[s.index('def sections('):s.index("assert sections(work/")],ns);parse=ns['sections'];results=[]
for name in ('default','partial'):
 case=out/name;seed=parse(work/name/'seed.route');final=parse(work/name/'output.route');assert set(seed)==set(final);total=sum(len(v) for v in seed.values());unchanged=sum(seed[n][pin]==final[n][pin] for n in seed for pin in seed[n]);log=(case/'run.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully' in log
 rows=[dict(zip(['iteration','net','nodes','overused','forced','fanout','first','lowfanout','hold'],map(int,m))) for m in re.findall(r'ROUTECAST_SELECT iter=(\d+) net=(\d+) nodes=(\d+) overused=(\d+) forced=(\d+) fanout=(\d+) first=(\d+) lowfanout=(\d+) hold=(\d+)',log)]
 results.append({'case':name,'total_paths':total,'unchanged_paths':unchanged,'changed_nets':[n for n in seed if seed[n]!=final[n]],'selected_net_visits':len(rows),'distinct_selected_nets':len({r['net'] for r in rows}),'selection_rows':rows})
files=[out/'receipt.json',root/'tools/verify_native_search_seed.py',Path(__file__)]
for name in ('default','partial'):files += [out/name/'physical_audit.json',out/name/'run.log',work/name/'seed.route',work/name/'output.route',work/name/'design.net',work/name/'design.place']
(out/'verification.json').write_text(json.dumps({'results':results,'hashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Final per-pin path preservation and native selection observations; unchanged final paths do not establish zero intermediate rerouting.'},indent=2)+'\n')
for r in results:print(r['case'],'unchanged',r['unchanged_paths'],'changed nets',len(r['changed_nets']),'selected distinct',r['distinct_selected_nets'])
