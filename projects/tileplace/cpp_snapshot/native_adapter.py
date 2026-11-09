"""C++ proposal adapter with Python differential checks for native orchestration.

The host still owns layout updates, feedback parsing and native acceptance.
This adapter must be separately recorded in provenance; it is not the sealed
Python implementation used for the historical experiments.
"""
import subprocess
from compare_proposals import TilePlaceV2Engine,payload,parse


def color_payload(engine,color,forbidden):
    lines=[payload(engine,color),
           ' '.join(map(str,[len(engine.focus_blocks),*sorted(engine.focus_blocks)])),
           str(len(forbidden))]
    for kind,units,trial in sorted(forbidden):
        values=[kind,len(units)]
        for unit in units:values.extend([len(unit),*unit])
        values.append(len(trial))
        for id,position in trial:values.extend([id,*position])
        lines.append(' '.join(map(str,values)))
    return '\n'.join(lines)+'\n'


class CheckedCppEngine(TilePlaceV2Engine):
    binary=None
    checks=[]
    def propose_color(self,color,forbidden_ids=None):
        forbidden=forbidden_ids or set()
        reference,stats=super().propose_color(color,forbidden)
        result=subprocess.run([str(self.binary),'--color'],input=color_payload(self,color,forbidden),
                              text=True,capture_output=True,check=True)
        actual=parse(result.stdout)
        expected=sorted((t.transaction_id,t.score_q20) for t in reference)
        if actual!=expected:raise RuntimeError(f'C++ proposal mismatch at color {color}')
        self.checks.append({'color':color,'selected':len(actual),'forbidden':len(forbidden),
                            'pressure_edges':len(self.pressure_q16),'timing_edges':len(self.path_edges_q16)})
        # Use C++ selection order, with host audit records verified above.
        by_id={t.transaction_id:t for t in reference}
        selected=[by_id[identity] for identity,score in sorted(actual,key=lambda row:(row[1],row[0]))]
        return selected,stats
