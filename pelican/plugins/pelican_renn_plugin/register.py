from pelican import signals
from docutils.parsers.rst import directives

from .projects_directive import (ProjectsDirective, ProjectDirective,
                                 retrieve_jinja_context)


def register():
    # projects directive
    signals.generator_init.connect(retrieve_jinja_context)
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)
