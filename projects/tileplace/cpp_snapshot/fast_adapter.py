"""C++ selection/statistics without Python enumeration of all candidates."""
from persistent_adapter import PersistentCppEngine
from compare_proposals import parse

class FastCppEngine(PersistentCppEngine):
    def propose_color(self,color,forbidden_ids=None):
        forbidden=forbidden_ids or set();values=[color,len(forbidden)]
        for kind,units,trial in sorted(forbidden):
            values.extend([kind,len(units)])
            for unit in units:values.extend([len(unit),*unit])
            values.append(len(trial))
            for id,p in trial:values.extend([id,*p])
        self._send('COLOR '+' '.join(map(str,values)))
        metrics=iter(self._line().split())
        eligible,proposals,accepted,rejected,kinds=(int(next(metrics)) for _ in range(5))
        counts={next(metrics):int(next(metrics)) for _ in range(kinds)}
        count=int(self._line());rows=[self._line() for _ in range(count)]
        if self._line()!='END' or count!=accepted:raise RuntimeError('C++ phase framing differs')
        actual=parse('\n'.join(rows));selected=[]
        for identity,score in sorted(actual,key=lambda row:(row[1],row[0])):
            kind,units,trial=identity
            # Compute audit deltas only for selected transactions, not candidates.
            transaction=self._make_transaction(kind,units,dict(trial))
            if transaction is None or transaction.transaction_id!=identity or transaction.score_q20!=score:
                raise RuntimeError('selected C++ transaction audit differs')
            selected.append(transaction)
        self._verify_layout()
        self.checks.append({'color':color,'selected':len(actual),'forbidden':len(forbidden),
                            'pressure_edges':len(self.pressure_q16),'timing_edges':len(self.path_edges_q16),
                            'python_full_candidate_enumeration':False})
        stats={'color':color,'eligible_units':eligible,'proposals':proposals,'accepted':accepted,
               'rejected_conflicts':rejected,'forbidden_transactions':len(forbidden),'accepted_kinds':counts}
        return selected,stats
