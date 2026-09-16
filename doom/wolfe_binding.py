"""Minimal access to the unchanged WOLFE C embedding API.

The C parser shares error scratch across model instances. All API operations
through this module are serialized; any other caller of the same C library
must also serialize access. No state file, correction, or feedback is used.
"""

import ctypes
import json
import os
import threading
from typing import Any


_API_LOCK = threading.Lock()
_OK = 0
_BUFFER_TOO_SMALL = 2
_NEURAL = 0
_REASONING_FULL = 1


class Wolfe:
    """A reusable C model; use as a context manager or call ``close()``."""

    def __init__(
        self,
        library: str | os.PathLike[str],
        tools: str | os.PathLike[str],
        examples: str | os.PathLike[str],
    ) -> None:
        self._handle = None
        self._lib = ctypes.CDLL(os.fspath(library))
        char_buffer = ctypes.POINTER(ctypes.c_char)
        self._lib.wolfe_load.argtypes = [
            ctypes.c_char_p,
            ctypes.c_char_p,
            ctypes.c_char_p,
            char_buffer,
            ctypes.c_size_t,
        ]
        self._lib.wolfe_load.restype = ctypes.c_void_p
        self._lib.wolfe_call.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_int,
            char_buffer,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        self._lib.wolfe_call.restype = ctypes.c_int
        self._lib.wolfe_error.argtypes = [ctypes.c_void_p]
        self._lib.wolfe_error.restype = ctypes.c_char_p
        self._lib.wolfe_free.argtypes = [ctypes.c_void_p]
        self._lib.wolfe_free.restype = None

        tools_bytes = os.fsencode(tools)
        examples_bytes = os.fsencode(examples)
        if b"\0" in tools_bytes or b"\0" in examples_bytes:
            raise ValueError("WOLFE definition paths must not contain NUL")
        error = ctypes.create_string_buffer(256)
        with _API_LOCK:
            self._handle = self._lib.wolfe_load(
                tools_bytes, examples_bytes, None, error, len(error)
            )
            if not self._handle:
                message = error.value.decode("utf-8", errors="replace")
                raise RuntimeError(f"WOLFE load failed: {message}")

    def call(self, text: str) -> dict[str, Any]:
        """Return the neural decision and full computed reasoning as JSON data."""
        if not isinstance(text, str):
            raise TypeError("WOLFE input must be text")
        if "\0" in text:
            raise ValueError("WOLFE input must not contain NUL")
        encoded = text.encode("utf-8")
        output = ctypes.create_string_buffer(4096)
        required = ctypes.c_size_t()
        with _API_LOCK:
            if not self._handle:
                raise RuntimeError("WOLFE model is closed")
            while True:
                status = self._lib.wolfe_call(
                    self._handle,
                    encoded,
                    _NEURAL,
                    _REASONING_FULL,
                    output,
                    len(output),
                    ctypes.byref(required),
                )
                if status == _OK:
                    result = json.loads(output.value.decode("utf-8"))
                    if not isinstance(result, dict):
                        raise RuntimeError("WOLFE returned a non-object response")
                    return result
                if status == _BUFFER_TOO_SMALL:
                    if required.value <= len(output):
                        raise RuntimeError("WOLFE reported an invalid buffer size")
                    output = ctypes.create_string_buffer(required.value)
                    continue
                error = self._lib.wolfe_error(self._handle)
                message = (error or b"unknown error").decode(
                    "utf-8", errors="replace"
                )
                raise RuntimeError(f"WOLFE call failed ({status}): {message}")

    def close(self) -> None:
        """Release the C model; repeated closes are harmless."""
        with _API_LOCK:
            if self._handle:
                self._lib.wolfe_free(self._handle)
                self._handle = None

    def __enter__(self) -> "Wolfe":
        with _API_LOCK:
            if not self._handle:
                raise RuntimeError("WOLFE model is closed")
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()
