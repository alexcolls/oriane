from __future__ import annotations

import atexit
import functools
import json
import os
import time

import psutil

try:
    from pynvml import nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlInit

    nvmlInit()
    _gpu = nvmlDeviceGetHandleByIndex(0)
except Exception:
    _gpu = None  # CPU-only host

_DATA: list[dict] = []


def _gpu_mem() -> int:
    if _gpu:
        return nvmlDeviceGetMemoryInfo(_gpu).used // 1_048_576  # MiB
    return 0


def profile(fn):
    """Decorator → measures wall, CPU, RAM, GPU; stores one row per call."""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        proc = psutil.Process(os.getpid())
        cpu_start = proc.cpu_times().user
        ram_start = proc.memory_info().rss // 1_048_576  # MiB
        gpu_start = _gpu_mem()

        t0 = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            dt = time.perf_counter() - t0
            cpu = proc.cpu_times().user - cpu_start
            ram = (proc.memory_info().rss // 1_048_576) - ram_start
            gpu = _gpu_mem() - gpu_start
            _DATA.append(
                {
                    "func": fn.__qualname__,
                    "sec": round(dt, 4),
                    "cpu": round(cpu, 4),
                    "ram": ram,
                    "gpu": gpu,
                }
            )

    return wrapper


def _dump_on_exit() -> None:
    from config.env_config import settings

    settings.reports_dir.mkdir(exist_ok=True)
    path = settings.reports_dir / f"perf-{time.strftime('%Y%m%d-%H%M%S')}.json"
    with open(path, "w") as f:
        json.dump(_DATA, f, indent=2)


atexit.register(_dump_on_exit)
