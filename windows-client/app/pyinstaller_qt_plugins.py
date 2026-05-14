import os
import sys


def _set_qt_plugin_path() -> None:
    base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    plugin_roots = [
        os.path.join(base_dir, "PySide6", "plugins"),
        os.path.join(base_dir, "PySide6", "Qt", "plugins"),
        os.path.join(base_dir, "plugins"),
    ]

    for plugin_root in plugin_roots:
        platforms_dir = os.path.join(plugin_root, "platforms")
        if os.path.exists(os.path.join(platforms_dir, "qwindows.dll")):
            os.environ["QT_PLUGIN_PATH"] = plugin_root
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = platforms_dir
            return


_set_qt_plugin_path()
