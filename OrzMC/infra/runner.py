import subprocess

class CommandResult:
    def __init__(self, code, stdout, stderr):
        self.code = code
        self.stdout = stdout
        self.stderr = stderr

class CommandRunner:
    def run(self, cmd, check = False, capture = True):
        if capture:
            res = subprocess.run(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
        else:
            res = subprocess.run(cmd, shell = True)
        if check and res.returncode != 0:
            raise RuntimeError(res.stderr)
        return CommandResult(res.returncode, res.stdout if capture else '', res.stderr if capture else '')

    def read(self, cmd):
        res = subprocess.run(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
        return res.stdout.strip()
