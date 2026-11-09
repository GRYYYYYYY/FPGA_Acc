"""Require freshly computed raw-prefix staging before each local invocation."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from source_binding_v2 import closure
from mmc_native_dirty_recipe_model_session_v1 import Session as Original
from fresh_native_warm_prefix_v1 import shared_prefix
class Session(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.sources.update(closure([Path(__file__)]));self._fresh_stage=None
 def attach_prefix(self,endpoint,route):
  self.prefix=shared_prefix(self,endpoint,route)
 def load_recipe(self,path,dirty):
  stage=self._fresh_stage
  if stage is None or str(Path(path).resolve())!=stage['recipe'] or set(dirty)!=stage['dirty']:raise RuntimeError('fresh raw prefix stage required')
  if self.owner.state is not stage['source_state'] or self.owner.generation!=stage['generation'] or self.prefix.calls!=stage['prefix_calls']:raise RuntimeError('stale fresh prefix stage')
  if sha(path)!=stage['recipe_hash'] or not all(sha(p)==h for p,h in stage['bindings'].items()):raise ValueError('fresh prefix inputs changed')
  result=json.loads(stage['encoded']);self.recipe_bindings=stage['bindings'];self._fresh_stage=None
  return result
 def close(self):
  if hasattr(self,'prefix'):self.prefix.close()
  super().close()
