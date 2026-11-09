"""Select worst-slack connections whose native delay regressed against baseline."""
import argparse,csv,hashlib,json
from pathlib import Path

def select(baseline,parent):
    if set(baseline)!=set(parent) or not parent:
        raise ValueError('Nonempty matching connection IDs required')
    for values in [baseline,parent]:
        for row in values.values():
            if row['delay_ps']<0 or not 0<=row['criticality_q']<=65535:
                raise ValueError('Invalid native delay or criticality')
    worst=min(v['slack_ps'] for v in parent.values())
    result=[]
    for task in sorted(parent):
        row=parent[task];delta=row['delay_ps']-baseline[task]['delay_ps']
        if row['slack_ps']==worst and delta>0:
            result.append({'task':task,'native_delay_increase_ps':delta,
                           'parent_slack_ps':worst,'parent_criticality_q':row['criticality_q']})
    return sorted(result,key=lambda v:(-v['native_delay_increase_ps'],v['task']))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path);parser.add_argument('parent',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args()
    def load(p):
        with p.open() as f:
            rows=list(csv.DictReader(f))
        values={int(v['task_id']):{k:int(x) for k,x in v.items()} for v in rows}
        if len(values)!=len(rows):raise ValueError('Duplicate connection ID')
        return values
    selected=select(load(a.baseline),load(a.parent))
    files=[a.baseline,a.parent,Path(__file__).resolve()]
    receipt={'status':'native_worst_slack_positive_regression_tasks_selected','selection_rule':'Minimum parent slack; positive native delay increase; descending delay increase, tie ascending taskID. All tasks satisfying the rule retained.','selected':selected,'source_sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Native roundedps observation selection only; no repair,representative validation,generalization or hardware claim.','research_complete':False}
    with a.output.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(selected))
if __name__=='__main__':main()
