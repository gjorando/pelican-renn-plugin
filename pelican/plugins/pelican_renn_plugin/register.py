from pelican import signals
from docutils.parsers.rst import directives

from .projects_directive import ProjectsDirective, ProjectDirective


def register():
    # projects directive
    directives.register_directive("projects", ProjectsDirective)
    directives.register_directive("project", ProjectDirective)
