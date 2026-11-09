"""Pinned lifecycle body with private design-core dependency injection."""
import ast,hashlib
from mmc_model_lifetime_v1 import Controller,SOURCE,SOURCE_SHA
from pre_route_endpoints import sha
class Model(Controller):
    def __init__(self,*args,overrides=None):
        if sha(SOURCE)!=SOURCE_SHA:raise ValueError('reference model source changed')
        tree=ast.parse(SOURCE.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict')
        loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='round_index')
        if ast.unparse(loop.iter)!='range(2)':raise ValueError('reference round schedule changed')
        resource="(id(search),id(criticality_graph))"
        loop.body.extend(ast.parse("assert context.active is None\nyield {'kind':'round','index':round_index,'file':str(file),'resources':"+resource+"}").body)
        i=fn.body.index(loop);fn.body[i:i]=ast.parse("yield {'kind':'ready','bindings':bindings,'resources':"+resource+"}").body
        original_body=fn.body
        final=ast.parse("if search is not None: search.close()\nif criticality_graph is not None: criticality_graph.close()\n_cleanup_report(search is None or search.closed,criticality_graph is None or criticality_graph.closed)").body
        fn.body=ast.parse('search=None\ncriticality_graph=None').body+[ast.Try(body=original_body,handlers=[],orelse=[],finalbody=final)]
        ast.fix_missing_locations(tree);self.cleanup={'calls':0,'search_closed':False,'graph_closed':False}
        def cleanup(a,b):self.cleanup.update(calls=self.cleanup['calls']+1,search_closed=a,graph_closed=b)
        ns={'__file__':str(SOURCE),'__name__':'mmc_lifetime_original','_cleanup_report':cleanup}
        self.transformed_ast_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()
        exec(compile(tree,str(SOURCE),'exec'),ns)
        if overrides is not None:ns.update(overrides)
        super().__init__(ns['predict'](*args))
