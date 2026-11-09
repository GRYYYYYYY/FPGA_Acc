"""Focused selection checks: slack ranking, regression sign, ties, invalid input."""
from select_regressed_critical_connections import select
import json

def row(delay,slack,criticality=65535):return {'delay_ps':delay,'slack_ps':slack,'criticality_q':criticality}
def main():
 baseline={9:row(100,-1),2:row(100,-1),5:row(0,-1),8:row(100,-1)}
 parent={9:row(110,-10),2:row(110,-10),5:row(9999,-9),8:row(99,-10)}
 assert [r['task'] for r in select(baseline,parent)]==[2,9]
 assert select(baseline,baseline)==[]
 assert select(dict(reversed(list(baseline.items()))),dict(reversed(list(parent.items()))))==select(baseline,parent)
 assert [r['task'] for r in select({1:row(0,-1),2:row(0,-1)},{1:row(2,-5,40000),2:row(999,-4,65535)})]==[1]
 for a,b in [({},{}),({1:row(1,-1)},{2:row(2,-1)}),({1:row(-1,-1)},{1:row(2,-1)}),({1:row(1,-1)},{1:row(2,-1,65536)})]:
  try:select(a,b)
  except ValueError:pass
  else:raise AssertionError('Invalid observations accepted')
 print(json.dumps({'status':'focused_critical_connection_selection_checks_pass','checks':8,'scope':'Selection behavior only; no unseen-case repair or quality evidence.'}))
if __name__=='__main__':main()
