#!/usr/bin/env python3
"""лаба 1: сбор данных ОС и запись их в json.

запуск:  python my_script.py
результат: файл system_info.json рядом со скриптом.

скрипт работает в Linux, macOS и Windows. данные берутся из стандартных модулей Python,
из системных файлов (/proc, реестр Windows) и из библиотеки psutil.
"""

import json
import os
import platform
import socket
import sys
from datetime import datetime

import psutil  # обоснование выбора - в README.md

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "system_info.json")


def to_gb(value):
    """байты -> гигабайты, округление до 2 знаков."""
    return round(value / (1024 ** 3), 2)


# 1. определение ОС
def detect_os():
    """возвращает 'linux', 'windows' или 'darwin' (так platform называет macOS)."""
    system = platform.system()
    if system not in ("Linux", "Windows", "Darwin"):
        sys.exit(f"неподдерживаемая ОС: {system}")
    return system


# 2. сбор параметров
def get_os_info(system):
    info = {
        "family": system,
        "release": platform.release(),
        "version": platform.version(),
        "architecture": platform.machine(),
        "hostname": socket.gethostname(),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="seconds"),
    }
    # параметры, которые есть только в конкретной ОС
    if system == "Linux":
        try:
            info["distro"] = platform.freedesktop_os_release().get("PRETTY_NAME")  # Python 3.10+
        except (OSError, AttributeError):
            info["distro"] = None
    elif system == "Windows":
        info["edition"] = platform.win32_edition()
    elif system == "Darwin":
        info["macos_version"] = platform.mac_ver()[0]
    return info


def get_cpu_model(system):
    """название процессора без вызова внешних утилит. none, если определить не удалось."""
    try:
        if system == "Linux":
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        elif system == "Windows":
            import winreg  # есть только в windows, поэтому импорт внутри функции
            path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
    except (OSError, ImportError):
        pass
    return None


def get_cpu_info(system):
    try:
        freq = psutil.cpu_freq()
        freq_mhz = round(freq.current, 1) if freq else None
    except Exception:  # на некоторых машинах (ARM, виртуалки) частота недоступна
        freq_mhz = None
    return {
        "model": get_cpu_model(system),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "frequency_mhz": freq_mhz,
        "usage_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "ram_total_gb": to_gb(ram.total),
        "ram_available_gb": to_gb(ram.available),
        "ram_used_percent": ram.percent,
        "swap_total_gb": to_gb(swap.total),
        "swap_used_percent": swap.percent,
    }


def get_disks_info():
    disks = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):  # например, пустой DVD-привод в windows
            continue
        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fstype": part.fstype,
            "total_gb": to_gb(usage.total),
            "free_gb": to_gb(usage.free),
            "used_percent": usage.percent,
        })
    return disks


def get_network_info():
    interfaces = {}
    for name, addrs in psutil.net_if_addrs().items():
        entry = {"ipv4": [], "ipv6": [], "mac": None}
        for addr in addrs:
            if addr.family == socket.AF_INET:
                entry["ipv4"].append(addr.address)
            elif addr.family == socket.AF_INET6:
                entry["ipv6"].append(addr.address)
            elif addr.family == psutil.AF_LINK:  # MAC-адрес
                entry["mac"] = addr.address
        interfaces[name] = entry
    return interfaces


def get_runtime_info():
    info = {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "process_count": len(psutil.pids()),
    }
    if hasattr(os, "getloadavg"):  # средняя загрузка есть только в linux/macos
        info["load_average_1_5_15"] = [round(x, 2) for x in os.getloadavg()]
    return info


def collect(system):
    return {
        "meta": {
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "script": os.path.basename(__file__),
        },
        "os": get_os_info(system),
        "cpu": get_cpu_info(system),
        "memory": get_memory_info(),
        "disks": get_disks_info(),
        "network": get_network_info(),
        "runtime": get_runtime_info(),
    }


# 3. запись в JSON
def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    system = detect_os()
    print(f"обнаружена ОС: {system}")
    data = collect(system)
    save_json(data, OUTPUT_FILE)
    print(f"результат сохранён в {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
