"""Fixed development readiness event; never a legal-route or native stop action."""
class ReadyGate:
 def __init__(self,identity):self.identity=dict(identity);self.iteration=0;self.streak=0;self.emitted=False
 def observe(self,identity,iteration,nodes,overused):
  if identity!=self.identity:raise ValueError('configuration/input/phase identity changed')
  if any(type(x) is not int for x in [iteration,nodes,overused]) or iteration!=self.iteration+1 or nodes<=0 or not 0<=overused<=nodes:raise ValueError('counter/sequence domain')
  self.iteration=iteration
  self.streak=self.streak+1 if iteration>=2 and 100*overused<=nodes else 0
  if self.streak>=2 and not self.emitted:self.emitted=True;return True
  return False
