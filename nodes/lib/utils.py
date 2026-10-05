"""Utility module for nodes."""

import os
import re
import logging
import tomllib
from pathlib import Path

from dotenv import load_dotenv


#################################################################
# Constants
#################################################################
ROOT_DIR = Path(__file__).parent.parent.parent

# `.env` is optional: load it when present, otherwise just use the OS
# environment. Nodes that actually need a credential read it at execution time
# and raise a clear error (shown as a ComfyUI error dialog) if it's still unset,
# so the pack always loads even without a `.env`.
_env_path = ROOT_DIR / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


def _package_name() -> str:
    """Read the pack name from `pyproject.toml`, falling back to the directory."""
    try:
        with open(ROOT_DIR / "pyproject.toml", "rb") as f:
            return tomllib.load(f)["project"]["name"]
    except Exception:
        return ROOT_DIR.name


PACKAGE_NAME = _package_name()


#################################################################
# Logger setup
#################################################################
# One logger for the whole pack, so the level is set in one place:
#     logging.getLogger(PACKAGE_NAME).setLevel(logging.DEBUG)
# The per-node label comes from the message, not from the logger name:
# `logger.info("[FilterTags] ...")` renders as `[<pack>/FilterTags]`.
# Untagged lines fall back to the module the call came from.
_NODE_TAG_RE = re.compile(r"^\[([^\]]+)\]\s*")


class _NodeTagFormatter(logging.Formatter):
    def format(self, record):
        message = record.getMessage()
        match = _NODE_TAG_RE.match(message)
        if match:
            node = match.group(1)
            message = message[match.end() :]
        else:
            node = record.module
        original = (record.msg, record.args)
        record.msg = f"[{PACKAGE_NAME}/{node}] {message}"
        record.args = ()
        try:
            return super().format(record)
        finally:
            record.msg, record.args = original


def get_logger(level: int = logging.INFO) -> logging.Logger:
    """Return the pack-wide logger, configuring its handler on first call."""
    logger = logging.getLogger(PACKAGE_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        # INFO/WARNING/ERROR are the levels actually used; 7 fits the longest.
        handler.setFormatter(
            _NodeTagFormatter(
                "%(asctime)s | %(levelname)-7s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False  # Prevent duplicate logs from root logger
    return logger


#################################################################
# Utility functions
#################################################################
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False


any_typ = AnyType("*")


def ensure_inside(base, path) -> None:
    """Raise if `path` resolves outside `base`.

    realpath on both, so neither ".." nor a symlink inside `base` gets out.
    """
    base = os.path.realpath(base)
    if os.path.commonpath([base, os.path.realpath(path)]) != base:
        raise ValueError(f"'{path}' is outside '{base}'")
