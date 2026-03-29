from .Client import Client
from .Server import Server
from ..domain import Step, Plan

class ClientUseCase:
    def __init__(self, config):
        self.client = Client(config)

    def plan(self):
        steps = [
            Step('prepare_client', lambda ctx: self.client.prepare_client() or ctx),
            Step('launch_client', lambda ctx: self.client.launch_client() or ctx)
        ]
        return Plan(steps)

class ServerUseCase:
    def __init__(self, config):
        self.server = Server(config)

    def plan(self):
        steps = [
            Step('management', self._management_step),
            Step('prepare_server', self._prepare_step),
            Step('launch_server', self._launch_step)
        ]
        return Plan(steps)

    def _management_step(self, ctx):
        if self.server.run_management_tasks():
            ctx['stop'] = True
        return ctx

    def _prepare_step(self, ctx):
        ctx['jar'] = self.server.prepare_server()
        return ctx

    def _launch_step(self, ctx):
        jar = ctx.get('jar')
        if jar:
            self.server.launch_server(jar)
        return ctx
