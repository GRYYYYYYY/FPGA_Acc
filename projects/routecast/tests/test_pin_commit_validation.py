import copy,unittest
from pin_commit_validation import validate
class CommitValidationTests(unittest.TestCase):
 def fixture(self):
  return ({'0':[10,2]},{'0':{'paths':{'2':[0]}}},[{'cid':0,'sink_class':10,'equivalent':'full','physical_members':[2,3]}],[{'connection_id':0,'sink':10}])
 def test_good_and_immutable(self):
  args=self.fixture();snapshot=copy.deepcopy(args);self.assertTrue(validate(*args));self.assertEqual(args,snapshot)
 def test_bad_class_member_and_non_equivalence(self):
  for mutation in ('class','member','none','boolean','missing'):
   chosen,paths,checks,endpoints=self.fixture()
   if mutation=='class':checks[0]['sink_class']=11
   if mutation=='member':checks[0]['physical_members']=[3]
   if mutation=='none':checks[0]['equivalent']='none'
   if mutation=='boolean':chosen['0']=[10,True]
   if mutation=='missing':paths['0']['paths']={}
   with self.assertRaises(ValueError):validate(chosen,paths,checks,endpoints)
 def test_duplicate_pin_and_cohort(self):
  chosen,paths,checks,endpoints=self.fixture();chosen['1']=[10,2];paths['1']=paths['0'];checks.append({**checks[0],'cid':1});endpoints.append({'connection_id':1,'sink':10})
  with self.assertRaises(ValueError):validate(chosen,paths,checks,endpoints)
  chosen['1']=[10,3];paths['1']={'paths':{'3':[1]}};self.assertTrue(validate(chosen,paths,checks,endpoints))
  del paths['1']
  with self.assertRaises(ValueError):validate(chosen,paths,checks,endpoints)
