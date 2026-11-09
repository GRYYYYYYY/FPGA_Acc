"""Persistent model session with explicitly certified native warm provenance."""
from persistent_native_model_session_v1 import Session as Original
from retained_native_warm_checkpoint_v1 import Checkpoint
from pathlib import Path
from source_binding_v2 import closure
class Session(Original):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.sources.update(closure([Path(__file__)]))
 def certify_checkpoint(self,initial,proof):
  self.checkpoint=Checkpoint(self,initial,proof)
 def reconstruct_warm(self,template,dirty):
  return self.checkpoint.reconstruct(template,dirty)
