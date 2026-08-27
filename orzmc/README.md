# orzmc

OrzMC core library: bootstrap Minecraft client / server, manage a sandboxed Java
runtime and multiple game versions. Framework-free, reusable, independently
published to PyPI.

```python
from orzmc import GameType, RuntimeOptions, launch_client

opts = RuntimeOptions(is_client=True, version="26.2", game_type="vanilla")
launch_client(opts)
```

See the [project README](../README.md) for full documentation.
