"""Sandbox-only stage transformer; final original VPR FULL/STA retained."""
from pathlib import Path
def transform(source,name,shared):
 if not name.startswith('trial_') or 'reference_canonical' in name:return source
 if 'native_import' in name:
  needle="binary=shared/'build_tileplace_vpr/vpr/vpr'";assert needle in source
  source=source.replace(needle,"binary=root/'build/native_route_sync_capture_v2_2026-10-06/routecast_sync_capture_vpr'")
  needle="with (work/'import.log').open('w') as f:code=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode";assert needle in source
  source=source.replace(needle,"with (work/'import.log').open('w') as f:code=subprocess.run(cmd,cwd=work,env={**env,'ROUTECAST_SYNC_CAPTURE_DIR':str(work)},stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode")
  source=source.replace('Fresh originalFULL/STA analysis','Instrumented capture FULL/STA analysis; original proof deferred to canonical reload')
 elif 'canonical_reload' in name:
  needle="capenv={**env,'ROUTECAST_SYNC_CAPTURE_DIR':str(cwd)};assert run(cmd,cwd,cwd/'capture.log',capenv)==0";assert needle in source
  source=source.replace(needle,"\n for n in ('before_sync.route','after_sync.route','design.net.post_routing'):shutil.copyfile(Path(row['cwd'])/n,cwd/n)\n shutil.copyfile(Path(row['cwd'])/'import.log',cwd/'capture.log')")
  binary=shared/'build_tileplace_vpr/vpr/vpr'
  source=source.replace("cmd[0]=row['command'][0];",'cmd[0]='+repr(str(binary))+';')
  source=source.replace("(capture,identity,Path(r['results'][0]['command'][0]))","(capture,identity,Path("+repr(str(binary))+"))")
 return source
