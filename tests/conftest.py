"""The ComfyUI modules the pack imports are stubbed so it imports outside
ComfyUI; nothing else is faked.
"""

import sys
import types
import importlib
import importlib.util
from pathlib import Path

import pytest

PACK_DIR = Path(__file__).resolve().parent.parent
PACK_NAME = "api_pack"


@pytest.fixture(scope="session")
def comfy_dirs(tmp_path_factory):
    """ComfyUI's output and user directories, side by side under one root."""
    root = tmp_path_factory.mktemp("comfy")
    dirs = types.SimpleNamespace(root=root, output=root / "output", user=root / "user")
    dirs.output.mkdir()
    (dirs.user / "default" / "workflows").mkdir(parents=True)
    return dirs


@pytest.fixture(scope="session")
def comfy_stubs(comfy_dirs):
    folder_paths = types.ModuleType("folder_paths")
    folder_paths.get_output_directory = lambda: str(comfy_dirs.output)
    folder_paths.get_user_directory = lambda: str(comfy_dirs.user)
    sys.modules["folder_paths"] = folder_paths

    graph = types.ModuleType("comfy_execution.graph")
    graph.ExecutionBlocker = type("ExecutionBlocker", (), {})
    sys.modules["comfy_execution"] = types.ModuleType("comfy_execution")
    sys.modules["comfy_execution.graph"] = graph

    latest = types.ModuleType("comfy_api.latest")
    latest.InputImpl = latest.io = latest.ui = types.SimpleNamespace()
    sys.modules["comfy_api"] = types.ModuleType("comfy_api")
    sys.modules["comfy_api.latest"] = latest


@pytest.fixture(scope="session")
def pack(comfy_stubs):
    """Imports a node module by name, the way ComfyUI would."""
    package = types.ModuleType(PACK_NAME)
    package.__path__ = [str(PACK_DIR)]
    sys.modules.setdefault(PACK_NAME, package)
    return lambda name: importlib.import_module(f"{PACK_NAME}.nodes.{name}")


@pytest.fixture(scope="session")
def mappings(comfy_stubs):
    """The pack's `__init__.py`, loaded the way ComfyUI loads a custom node."""
    spec = importlib.util.spec_from_file_location(
        PACK_NAME, PACK_DIR / "__init__.py", submodule_search_locations=[str(PACK_DIR)]
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACK_NAME] = module
    spec.loader.exec_module(module)
    return module.NODE_CLASS_MAPPINGS
