"""Atomic explicit-path batch ledger, reference implementation.

Stage all removals before replacements to support a whole net changing SOURCE.
Uses full copied state; no claim of low-cost dirty update or legal route trees.
"""
from collections.abc import Mapping
from connection_golden import Result,UINT64_MAX,integer
from rr_occupancy import Occupancy


class BatchOccupancy(Occupancy):
    def fork(self):
        """Independent proposal ledger sharing immutable graph/connection records."""
        branch=BatchOccupancy(self.graph)
        branch._states=dict(self._states)
        branch._refs=self._refs.copy()
        branch._occupancy=self._occupancy.copy()
        return branch

    def update_batch(self,updates):
        if not isinstance(updates,(list,tuple)) or not updates:return Result.INVALID
        seen=set();prepared=[]
        for row in updates:
            if not isinstance(row,Mapping):return Result.INVALID
            if set(row)-{'connection_id','epoch','net_id','source','sink','edge_ids','remove'}:return Result.INVALID
            cid=row.get('connection_id');epoch=row.get('epoch');remove=row.get('remove',False)
            if not integer(cid,0,UINT64_MAX) or not integer(epoch,1,UINT64_MAX) or type(remove) is not bool or cid in seen:return Result.INVALID
            seen.add(cid);old=self._states.get(cid)
            if old is not None and epoch<=old[0]:return Result.STALE
            prepared.append((dict(row),old))
        staged=Occupancy(self.graph)
        staged._states=dict(self._states);staged._refs=self._refs.copy();staged._occupancy=self._occupancy.copy()
        for row,old in prepared:
            result=staged.update(row['connection_id'],row['epoch'],remove=True)
            if result!=Result.COMMITTED:return result
        for row,old in prepared:
            cid=row['connection_id']
            if row.get('remove',False):
                if any(row.get(k) is not None for k in ('net_id','source','sink','edge_ids')):return Result.INVALID
                continue
            # Retain pre-transaction epoch for final replacement validation.
            if old is None:staged._states.pop(cid)
            else:staged._states[cid]=(old[0],None)
            result=staged.update(**row)
            if result!=Result.COMMITTED:return result
        if staged.occupancy!=staged.rebuild():raise AssertionError('batch net union mismatch')
        self._states=staged._states;self._refs=staged._refs;self._occupancy=staged._occupancy
        return Result.COMMITTED
