class Step:
    def __init__(self, name, action):
        self.name = name
        self.action = action

    def run(self, ctx):
        result = self.action(ctx)
        return result if result is not None else ctx

class Plan:
    def __init__(self, steps):
        self.steps = steps

    def run(self):
        ctx = {}
        for step in self.steps:
            if ctx.get('stop'):
                break
            ctx = step.run(ctx)
        return ctx
