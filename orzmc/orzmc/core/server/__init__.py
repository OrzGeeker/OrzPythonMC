"""Server-core acquisition strategies (``CoreProvider`` registry).

Importing this package registers the vanilla / paper / fabric / forge
providers so ``CoreProvider.for_type`` resolves them. This is library-internal
— none of these names are part of the public API contract in ``orzmc/__init__``.
"""

from orzmc.core.server.base import BuildJavaSeam, CoreProvider, DownloadSeam, ServerPrepare
from orzmc.core.server.fabric import FabricProvider
from orzmc.core.server.forge import ForgeProvider
from orzmc.core.server.paper import PaperProvider
from orzmc.core.server.vanilla import VanillaProvider

__all__ = [
    "BuildJavaSeam",
    "CoreProvider",
    "DownloadSeam",
    "FabricProvider",
    "ForgeProvider",
    "PaperProvider",
    "ServerPrepare",
    "VanillaProvider",
]
