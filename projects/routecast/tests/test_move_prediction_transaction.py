import unittest
from dataclasses import replace
from move_prediction_transaction import MoveState, MovePredictionTransaction

class MovePublicationTests(unittest.TestCase):
    def initial(self):
        return MoveState(0,'a'*64,b'place',b'endpoints',b'paths',b'budget',b'pressure',b'old cache')
    def test_failures_preserve_entire_snapshot(self):
        old=self.initial();tx=MovePredictionTransaction(old)
        def fail(state):raise RuntimeError('stage failure')
        self.assertEqual(tx.commit(0,fail,lambda s:True),'FAILED')
        candidate=replace(old,epoch=1,placement=b'new',prediction=b'new paths',search_cache=b'new cache')
        self.assertEqual(tx.commit(0,lambda s:candidate,lambda s:False),'REJECTED')
        self.assertEqual(tx.commit(0,lambda s:candidate,fail),'FAILED')
        self.assertIs(tx.snapshot(),old)
        self.assertEqual(tx.commit(0,lambda s:replace(candidate,context='b'*64),lambda s:True),'CONTEXT_CHANGE')
        self.assertEqual(tx.commit(0,lambda s:candidate,lambda s:True),'COMMITTED')
        self.assertIs(tx.snapshot(),candidate)
        self.assertEqual(tx.commit(0,fail,lambda s:True),'STALE')
    def test_reentry_and_mutable_payload_rejected(self):
        old=self.initial();tx=MovePredictionTransaction(old);new=replace(old,epoch=1)
        def validate(state):
            self.assertEqual(tx.commit(0,lambda s:new,lambda s:True),'BUSY')
            return True
        self.assertEqual(tx.commit(0,lambda s:replace(new,prediction=b'outer'),validate),'COMMITTED')
        self.assertEqual(tx.snapshot().prediction,b'outer')
        with self.assertRaises(ValueError):replace(old,prediction=bytearray(b'mutable'))
        with self.assertRaises(ValueError):replace(old,search_cache=bytearray(b'mutable'))
if __name__=='__main__':unittest.main()
