import hashlib

from docutils import nodes
from docutils.frontend import OptionParser, Values
from docutils.writers.html5_polyglot import HTMLTranslator
from docutils.core import publish_parts
from docutils.utils import new_document
from docutils.parsers.rst import Directive, directives
from jinja2 import PackageLoader
from pelican.plugins.i18n_subsites import relpath_to_site

from .jinja_filters import parse_link

jinja_env = None
jinja_context = None
readers = None

def register_templates(generator):
    """
    Callable for the `generator_init` signal that retrieves the jinja environment and
    settings from the generator.

    :param generator: The generator instance.
    """

    global jinja_env
    global jinja_context
    global readers
    jinja_env = generator.env
    jinja_context = generator.settings
    readers = generator.readers

    jinja_env.loader.loaders.append(PackageLoader("pelican_renn_plugin", "templates"))


class ProjectDirective(Directive):
    """
    A nested directive for the `ProjectsDirective`, that creates a single element.
    """

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True
    option_spec = {
        "links": directives.unchanged,
        "image": directives.uri,
        "template": directives.unchanged,
    }
    has_content = True

    def run(self):
        """
        Create a list element for the project.
        """

        template = jinja_env.get_template(self.options.get(
            "template",
            "snippets/project.html"
        ))

        # Ensure we are inside a projects-modal
        if not "projects-temp-container" in self.state.parent["classes"]:
            return [self.state_machine.reporter.error(
                "Found a 'project' directive outside of 'projects'",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno
            )]

        title = self.arguments[0]
        try:
            image = self.options["image"]
        except KeyError:
            raise AttributeError("Missing option 'image'")
        raw_links = self.options.get("links", "")
        links = [parse_link(link.strip()) for link in
                 raw_links.split(",")] if raw_links else []

        # ID of the popover, which should be (probably) unique
        popover_id = f"project-{hashlib.md5(str(id(self)).encode()).hexdigest()}"

        # Settings for rendering the project popover content
        settings = self.state.document.settings.copy()
        # The popover title is level 2
        settings.initial_header_level = "3"

        return [nodes.raw("", template.render(
            project_title=title,
            project_image=image,
            project_links=links,
            project_content=publish_parts(
                source="\n".join(self.content),
                writer_name="html5",
                settings=settings,
            )["fragment"],
            popover_id=popover_id,
            # For some fucking reason this is not present in jinja_context, hence the
            # manual inclusion to the render context (I hate this library omg)
            relpath_to_site=relpath_to_site,
            **jinja_context
        ), format="html")]


class ProjectsDirective(Directive):
    """
    A directive that creates a project list modal.
    """

    has_content = True

    option_spec = {
        "template": directives.unchanged,
    }

    def run(self):
        """
        Create a bullet list node and populate it with the contents of the directive.
        """

        template = jinja_env.get_template(self.options.get(
            "template",
            "snippets/projects.html"
        ))

        container = nodes.container(classes=["projects-temp-container"])
        self.state.nested_parse(self.content, self.content_offset, container)

        wrapped = []
        # Move non list items to put them in the wrapper
        # We iterate in reverse as to not break the iteration if a child is removed
        for child in reversed(container.children):
            if not isinstance(child, nodes.raw):
                container.remove(child)
                child["classes"].append("mb-4")
                doc = new_document(
                    "",
                    self.state.document.settings.copy()
                )
                doc += child
                translator = HTMLTranslator(doc)
                child.walkabout(translator)
                wrapped.append("".join(translator.body))

        return [nodes.raw("", template.render(
            projects=[c.astext() for c in container.children],
            wrapped=reversed(wrapped),
            **jinja_context
        ), format="html")]
