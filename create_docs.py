import os
import pathlib

import django
import pdoc

if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "ecstasy_project.settings"
    django.setup()

    doc = pdoc.pdoc(
        "accounting",
        "!accounting.migrations",
        "app_settings",
        "!app_settings.migration",
        "check",
        "!check.migration",
        "!check.tests",
        "devicemanager",
        "!devicemanager.tests",
        "gathering",
        "!gathering.migrations",
        "gpon",
        "!gpon.migrations",
        "maps",
        "!maps.migrations",
        "net_tools",
        "!net_tools.migration",
        "news",
        "!news.migrations",
        "ring_manager",
        "!ring_manager.migration",
        output_directory=pathlib.Path(__file__).parent / "static" / "docs",
    )
