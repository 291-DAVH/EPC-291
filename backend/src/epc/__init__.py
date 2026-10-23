"""EPC-291 backend: a modular monolith. Each package under epc.modules is a bounded context that
exposes only its `public` module to the others (enforced by import-linter, see backend/.importlinter)."""
__version__ = "0.1.0"
