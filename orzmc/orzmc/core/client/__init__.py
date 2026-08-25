"""Client add-on strategies (``ClientProvider`` registry).

Importing this package registers the vanilla / fabric / forge providers so
``ClientProvider.for_type`` resolves them. Library-internal — none of these
names are part of the public API contract in ``orzmc/__init__``.
"""

from orzmc.core.client.base import BuildJavaSeam, ClientPrepare, ClientProvider, DownloadSeam
from orzmc.core.client.fabric import FabricProvider
from orzmc.core.client.forge import ForgeProvider
from orzmc.core.client.vanilla import VanillaProvider

__all__ = [
    "BuildJavaSeam",
    "ClientPrepare",
    "ClientProvider",
    "DownloadSeam",
    "FabricProvider",
    "ForgeProvider",
    "VanillaProvider",
]
