"""Rapidfood backend modules package.

Each subpackage is an isolated bounded context following Hexagonal
Architecture (Ports & Adapters).

Cross-module dependencies are expressed through application ports.
Adapters provide the concrete integration between modules; modules must never
depend directly on another module's domain, infrastructure adapters, or
internal use cases.
"""