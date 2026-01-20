import os
import re

from pelican import signals
from docutils.parsers.rst import directives

from .projects_directive import ProjectsDirective, ProjectDirective, parse_link
from .hidden_category import create_hidden_categories


def set_default_settings(instance):
    """
    Signal that initializes our plugin default settings.

    :param instance: The Pelican instance.
    """

    # hidden categories settings
    instance.settings.setdefault("HIDDENCATEGORY_ENABLE", False)
    instance.settings.setdefault("HIDDENCATEGORY_NAME", "{base_category}-full")
    url_parent, url_name = os.path.split(instance.settings["CATEGORY_URL"])
    instance.settings.setdefault(
        "HIDDENCATEGORY_URL",
        f"{url_parent}-full/{url_name}"
    )
    sa_parent, sa_name = os.path.split(instance.settings["HIDDENCATEGORY_URL"])
    instance.settings.setdefault(
        "HIDDENCATEGORY_SAVE_AS",
        f"{sa_parent}/{sa_name if sa_name else "index.html"}"
    )
    instance.settings.setdefault("HIDDENCATEGORY_OVERRIDES", dict())
    instance.settings.setdefault("HIDDENCATEGORY_EXCLUDES", [])

    # lander page settings
    instance.settings.setdefault("LANDER_ENABLE", False)
    instance.settings.setdefault("LANDER_PATHS", ["lander"])
    instance.settings.setdefault("LANDER_EXCLUDES", [])
    instance.settings.setdefault("LANDER_SAVE_AS", "lander.html")

    # Automatically exclude lander page paths from the articles
    for path in instance.settings["LANDER_PATHS"]:
        if path not in instance.settings["ARTICLE_EXCLUDES"]:
            instance.settings["ARTICLE_EXCLUDES"].append(path)


def register_filters(generator):
    """
    Signal that registers the custom jinja filters.
    """

    generator.env.filters["parse_link"] = parse_link


def register():
    # global
    signals.initialized.connect(set_default_settings)

    # projects directive
    signals.generator_init.connect(register_filters)
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)

    # hidden categories
    signals.article_generator_finalized.connect(create_hidden_categories)
