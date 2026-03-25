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
        "apps.app_settings",
        "!app_settings.migration",
        "apps.check",
        "!check.migration",
        "!check.tests",
        "devicemanager",
        "!devicemanager.tests",
        "apps.gathering",
        "!gathering.migrations",
        "apps.gpon",
        "!gpon.migrations",
        "apps.maps",
        "!maps.migrations",
        "apps.net_tools",
        "!net_tools.migration",
        "apps.news",
        "!news.migrations",
        "apps.ring_manager",
        "!ring_manager.migration",
        output_directory=pathlib.Path(__file__).parent / "static" / "docs",
    )
