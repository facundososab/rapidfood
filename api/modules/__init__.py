"""Rapidfood backend modules package.

Each subpackage is an isolated bounded context following Hexagonal
Architecture (Ports & Adapters). Cross-module communication happens ONLY
through application ports, never through internal adapters/domain/use_cases.
"""