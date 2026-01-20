from pelican import signals
from docutils.parsers.rst import directives

from .projects_directive import ProjectsDirective, ProjectDirective
from .hidden_category import create_hidden_categories, set_default_settings


def register():
    # projects directive
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)

    # hidden categories
    signals.article_generator_finalized.connect(create_hidden_categories)
    signals.initialized.connect(set_default_settings)
