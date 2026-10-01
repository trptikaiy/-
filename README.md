# лабораторная работа 1. сбор данных ОС

скрипт определяет, в какой операционной системе он запущен (linux, macOS или windows), собирает параметры системы и записывает их в файл `system_info.json`.

## запуск

```
pip install -r requirements.txt
python my_script.py
```

результат появится в файле `system_info.json` рядом со скриптом. требуется python 3.8+ (название дистрибутива linux определяется через python 3.10+, на более старых версиях поле будет `null`).

## ограничения задания и как они выполнены

- утилиты ОС (`systeminfo`, `lscpu`, `uname`, `wmic` и т.п.) не используются, `subprocess` в скрипте нет.
- основа - стандартные модули: `platform`, `socket`, `os`, `json`, `datetime`, `winreg` (только Windows).
- название процессора читается напрямую: из `/proc/cpuinfo` в linux и из реестра windows через `winreg`.
- внешний модуль один - `psutil`.

## почему psutil, а не стандартные модули

стандартная библиотека Python не даёт кроссплатформенных данных о ресурсах системы:

| параметр | что есть в стандартной библиотеке | что пришлось бы делать без psutil |
|---|---|---|
| оперативная память | ничего | linux: парсить `/proc/meminfo`; windows: вызывать winAPI через `ctypes`; macOS: `sysctl` |
| загрузка процессора | ничего | linux: считать разницу в `/proc/stat`; windows: счётчики производительности |
| список дисков и место | только `shutil.disk_usage` для одного известного пути | искать точки монтирования отдельно для каждой ОС |
| сетевые интерфейсы | только `socket.gethostname()` | `/sys/class/net`, `GetAdaptersAddresses`, `getifaddrs` |
| время загрузки, число процессов | ничего | отдельная реализация под каждую ОС |

`psutil` решает всё это одним интерфейсом для всех трёх ОС и сам читает данные из `/proc`, winAPI и системных вызовов, не запуская внешние программы. Так код получается короче и надёжнее, чем три самописные реализации.

## собираемые параметры

структура JSON: пять основных разделов и служебный `meta`.

**meta**
- `collected_at` - дата и время сбора
- `script` - имя скрипта

**os** - операционная система
- `family` - linux / windows / darwin (macOS)
- `release`, `version` - релиз и версия ядра/сборки
- `architecture` - архитектура (x86_64, AMD64, arm64)
- `hostname` - имя компьютера
- `boot_time` - время последней загрузки
- только linux: `distro` - название дистрибутива
- только windows: `edition` - редакция (Home, Pro и т.д.)
- только macOS: `macos_version` - версия macOS

**cpu** - процессор
- `model` - название модели (в macOS и на некоторых ARM-системах может быть `null`)
- `physical_cores`, `logical_cores` - число физических и логических ядер
- `frequency_mhz` - текущая частота
- `usage_percent` - загрузка за 1 секунду

**memory** - память
- `ram_total_gb`, `ram_available_gb`, `ram_used_percent`
- `swap_total_gb`, `swap_used_percent`

**disks** - список разделов, для каждого:
- `device`, `mountpoint`, `fstype`
- `total_gb`, `free_gb`, `used_percent`

**network** - сетевые интерфейсы, для каждого:
- `ipv4`, `ipv6` - списки адресов
- `mac` - MAC-адрес

**runtime** - окружение
- `python_version`, `python_implementation`
- `process_count` - число запущенных процессов
- `load_average_1_5_15` - средняя загрузка за 1/5/15 минут (только Linux и macOS)

такой набор данных выбран, чтобы описать систему полностью (ОС, процессор, память, диски, сеть) и не раздувать отчёт малополезными деталями.

## пример результата

```json
{
  "meta": {"collected_at": "2026-09-30T12:00:00", "script": "my_script.py"},
  "os": {"family": "Linux", "release": "6.5.0", "architecture": "x86_64", "distro": "Ubuntu 22.04.3 LTS"},
  "cpu": {"model": "Intel(R) Core(TM) i5-1135G7", "physical_cores": 4, "logical_cores": 8},
  "memory": {"ram_total_gb": 15.5, "ram_used_percent": 42.1}
}
```

(показаны не все поля)
