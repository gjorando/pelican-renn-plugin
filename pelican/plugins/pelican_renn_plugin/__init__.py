import os

from pelican import signals, ArticlesGenerator
from docutils.parsers.rst import directives
from pelican.plugins.i18n_subsites import article2draft

from .jinja_filters import parse_link, get_flag_emoji
from .projects_directive import ProjectsDirective, ProjectDirective
from .hidden_category import create_hidden_categories
from .noindex_category import patch_generate_direct_templates


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

    # # We need to update this parameter so that the i18n subsites plugin takes into account hidden articles in its untranslated policy
    instance.settings.setdefault("I18N_GENERATORS_INFO", {
        ArticlesGenerator: {
            "translations_lists": ["translations", "drafts_translations",
                                   "hidden_translations"],
            "contents_lists": [("articles", "drafts"), ("hidden_articles", "drafts")],
            "hiding_func": article2draft,
            "policy": "I18N_UNTRANSLATED_ARTICLES",
        },
    })

    # no-index categories
    instance.settings.setdefault("NOINDEX_CATEGORIES", [])


def register_filters(generator):
    """
    Signal that registers the custom jinja filters.
    """

    generator.env.filters["parse_link"] = parse_link
    generator.env.filters["get_flag_emoji"] = get_flag_emoji


def register():
    # global
    signals.initialized.connect(set_default_settings)

    # projects directive
    signals.generator_init.connect(register_filters)
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)

    # hidden categories
    signals.article_generator_finalized.connect(create_hidden_categories)

    # noindex categories
    signals.article_generator_init.connect(patch_generate_direct_templates)
