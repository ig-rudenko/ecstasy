import django
import pdoc
import os
import pathlib


if __name__ == "__main__":
    os.environ["DJANGO_SETTINGS_MODULE"] = "ecstasy_project.settings"
    django.setup()

    doc = pdoc.pdoc(
        "app_settings",
        "!app_settings.migration",
        "check",
        "!check.migration",
        "!check.tests",
        "devicemanager",
        "!devicemanager.tests",
        "net_tools",
        "!net_tools.migration",
        "maps",
        "!maps.migration",
        "gathering",
        "!gathering.migration",
        output_directory=pathlib.Path(__file__).parent / "static" / "docs",
    )
