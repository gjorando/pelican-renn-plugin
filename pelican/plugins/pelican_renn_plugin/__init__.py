import os
from importlib import import_module

from pelican import signals, ArticlesGenerator
from docutils.parsers.rst import directives
from pelican.plugins.i18n_subsites import article2draft

from .jinja_filters import parse_link, get_flag_emoji, register_filters
from .projects_directive import ProjectsDirective, ProjectDirective, register_templates
from .hidden_category import create_hidden_categories
from .noindex_category import patch_generate_direct_templates
from .tailwindcss import load_tailwind, compile_css
from .html5_reader import patch_reader
from .thumbnail import generate_thumbnails, load_pillow
from .overrides import (override_page_context, restore_page_context,
                        patch_generate_categories)


def set_default_settings(instance):
    """
    Signal that initializes our plugin default settings.

    :param instance: The Pelican instance.
    """

    # Hidden categories settings
    instance.settings.setdefault("HIDDENCATEGORY_ENABLE", False)
    instance.settings.setdefault("HIDDENCATEGORY_NAME", "{base_category} (full)")
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
    instance.settings.setdefault("HIDDENCATEGORY_EXCLUDES", [])

    # We need to update this parameter so that the i18n subsites plugin takes into account hidden articles in its untranslated policy
    instance.settings.setdefault("I18N_GENERATORS_INFO", {
        ArticlesGenerator: {
            "translations_lists": ["translations", "drafts_translations",
                                   "hidden_translations"],
            "contents_lists": [("articles", "drafts"), ("hidden_articles", "drafts")],
            "hiding_func": article2draft,
            "policy": "I18N_UNTRANSLATED_ARTICLES",
        },
    })

    # No-index categories
    instance.settings.setdefault("NOINDEX_CATEGORIES", [])

    # Tailwind CSS
    instance.settings.setdefault("TAILWINDCSS_ENABLE", False)
    instance.settings.setdefault("TAILWINDCSS_VERSION", "latest")
    instance.settings.setdefault("TAILWINDCSS_CONFIG", None)
    instance.settings.setdefault("TAILWINDCSS_INPUT_FILES", [])
    instance.settings.setdefault("TAILWINDCSS_MINIFY", True)

    # HTML 5
    instance.settings.setdefault("HTML5_ENABLE", True)

    # Thumbnail
    instance.settings.setdefault("THUMBNAIL_ENABLE", False)
    instance.settings.setdefault("THUMBNAIL_SAVE_AS",
                                 "{parent}/thumbnails/{stem}_{resize}{suffix}")
    # FIXME would be better if this was relative to the content path, and we were resolving each path to its destination path in OUTPUT_PATH
    instance.settings.setdefault("THUMBNAIL_PATHS", ["images"])
    instance.settings.setdefault("THUMBNAIL_RESIZES", {
        "square": (150, True),  # Cropped square of size 150x150px
        "wide": (150, None, True),  # Keep aspect ratio and set width to 150px
        "tall": (None, 150, True),  # Keep aspect ratio and set height to 150px
    })
    instance.settings.setdefault("THUMBNAIL_SKIP_EXISTING", True)

    # Overrides
    instance.settings.setdefault("OVERRIDES", dict())


def register():
    # global
    signals.initialized.connect(set_default_settings)
    signals.generator_init.connect(register_filters)

    # projects directive
    signals.generator_init.connect(register_templates)
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)

    # hidden categories
    signals.article_generator_finalized.connect(create_hidden_categories)

    # noindex categories
    signals.article_generator_init.connect(patch_generate_direct_templates)

    # Tailwind CSS
    signals.initialized.connect(load_tailwind)
    signals.finalized.connect(compile_css)

    # HTML5 RST reader
    signals.readers_init.connect(patch_reader)

    # Thumbnail
    signals.initialized.connect(load_pillow)
    signals.finalized.connect(generate_thumbnails)

    # Overrides
    signals.page_generator_write_page.connect(override_page_context)
    signals.page_writer_finalized.connect(restore_page_context)
    signals.article_generator_init.connect(patch_generate_categories)
