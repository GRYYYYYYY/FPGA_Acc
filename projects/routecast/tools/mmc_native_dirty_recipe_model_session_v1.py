"""Authenticated dirty-only transport on retained native model session."""
from compact_persistent_native_model_session_v1 import Session as Original
from native_dirty_recipe_checkpoint_v1 import Checkpoint
from pathlib import Path
from source_binding_v2 import closure
class Session(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.sources.update(closure([Path(__file__)]))
 def certify_checkpoint(self,initial,proof):self.checkpoint=Checkpoint(self,initial,proof)
 def load_recipe(self,path,dirty):
  result,bindings=self.checkpoint.from_recipe(path,dirty)
  self.recipe_bindings=bindings
  return result
