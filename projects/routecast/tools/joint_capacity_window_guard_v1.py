"""Immutable original exploration-window check; not a candidate acceptance gate."""
import datetime as dt,json,hashlib,argparse
from pathlib import Path
R=Path(__file__).resolve().parents[1]
DEFAULT=R/'experiments/joint_capacity_direction_review_v2_2026-10-21/window_anchor.json'
def timestamp(value):
 x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
 if x.tzinfo is None:raise ValueError('timezone-aware UTC timestamp required')
 return x.astimezone(dt.timezone.utc)
def load_anchor(path=DEFAULT):
 a=json.loads(Path(path).read_text());p=Path(a['source']);actual=hashlib.sha256(p.read_bytes()).hexdigest()
 if actual!=a['source_sha256']:raise ValueError('Original stop-loss source hash changed; window cannot be reset')
 original=json.loads(p.read_text())['stop_loss']
 for k in ['recorded_utc','review_no_later_than_utc']:
  if original[k]!=a[k]:raise ValueError('Original window fields differ from anchor')
 start=timestamp(a['recorded_utc']);end=timestamp(a['review_no_later_than_utc'])
 if not start+dt.timedelta(days=2)<=end<=start+dt.timedelta(days=3):raise ValueError('Window must retain original2-3day span')
 return a
def assess(a,now):
 if now.tzinfo is None:raise ValueError('timezone-aware current time required')
 now=now.astimezone(dt.timezone.utc);start=timestamp(a['recorded_utc']);end=timestamp(a['review_no_later_than_utc'])
 if now<start:raise ValueError('Current time precedes original recorded exploration start')
 open_=now<end;review=now>=start+dt.timedelta(days=2)
 return {'now_utc':now.isoformat(),'recorded_utc':start.isoformat(),'review_window_opens_utc':(start+dt.timedelta(days=2)).isoformat(),'hard_deadline_utc':end.isoformat(),'new_exploratory_launch_permitted_by_time':open_,'two_day_review_window_reached':review,'status':'CLOSED_REQUIRE_STOP_LOSS_REVIEW' if not open_ else 'REVIEW_WINDOW_OPEN' if review else 'EXPLORATION_WINDOW_OPEN','seconds_remaining':max(0,(end-now).total_seconds()),'scope':'Time permission only; does not authorize repeats of rejected mechanisms or prove candidate capacity, quality, cost or whole-goal completion.'}
def require_open(path=DEFAULT):
 result=assess(load_anchor(path),dt.datetime.now(dt.timezone.utc))
 if not result['new_exploratory_launch_permitted_by_time']:raise RuntimeError('Joint-capacity exploration deadline reached: stop new launches and finalize evidence review')
 return result
if __name__=='__main__':
 argparse.ArgumentParser(description=__doc__).parse_args();result=assess(load_anchor(),dt.datetime.now(dt.timezone.utc));print(json.dumps(result,indent=2));raise SystemExit(0 if result['new_exploratory_launch_permitted_by_time'] else 2)
