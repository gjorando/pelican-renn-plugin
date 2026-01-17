import re

from jinja2 import PackageLoader
from docutils import nodes
from docutils.core import publish_parts
from docutils.parsers.rst import Directive, directives

jinja_env = None
jinja_settings = None


def parse_link(raw):
    """
    Small function that parses a raw link (`text <uri>` or `uri`).
    """

    match = re.match(r"^(.*)\s*<([^>]+)>$", raw)
    if not match:
        raise ValueError(f"Invalid link format '{raw}'")
    uri = match[2]
    title = match[1] if match[1] else match[2]
    return title.strip(), uri.strip()


def retrieve_jinja_context(generator):
    """
    Callable for the `generator_init` signal that retrieves the jinja environment and
    settings from the generator.
    """

    global jinja_env
    global jinja_settings
    jinja_env = generator.env
    jinja_settings = generator.settings

    jinja_env.loader.loaders.append(PackageLoader(
        "pelican_renn_plugin",
        "templates"
    ))


class ProjectDirective(Directive):
    """
    A nested directive for the `ProjectsDirective`, that creates a single element.
    """

    required_arguments = 0
    option_spec = {
        "title": str,
        "links": directives.unchanged,
        "image": directives.uri
    }
    has_content = True

    def run(self):
        """
        Create a list element for the project.
        """

        template = jinja_env.get_template("pelican_renn_plugin/project.html")

        if not "projects-temp-container" in self.state.parent["classes"]:
            return [self.state_machine.reporter.error(
                "Found a 'project' directive outside of 'projects'",
                nodes.literal_block(self.block_text, self.block_text),
                line=self.lineno
            )]

        try:
            title = self.options["title"]
        except KeyError:
            raise AttributeError("Missing option 'title'")
        try:
            image = self.options["image"]
        except KeyError:
            raise AttributeError("Missing option 'image'")
        raw_links = self.options.get("links", "")
        links = [parse_link(link.strip()) for link in
                 raw_links.split(",")] if raw_links else []

        anchor = f"projects-popup-{title.lower().replace(" ", "-")}"

        return [nodes.raw("", template.render(
            project_title=title,
            project_image=image,
            project_links=links,
            project_anchor=anchor,
            project_content=publish_parts(
                source="\n".join(self.content),
                writer_name="html",
                settings_overrides={
                    "initial_header_level": 3
                }
            )["fragment"],
            **jinja_settings
        ), format="html")]


class ProjectsDirective(Directive):
    """
    A directive that creates a project list modal.
    """

    has_content = True

    def run(self):
        """
        Create a bullet list node and populate it with the contents of the directive.
        """

        template = jinja_env.get_template("pelican_renn_plugin/projects.html")

        container = nodes.container(classes=["projects-temp-container"])
        self.state.nested_parse(self.content, self.content_offset, container)

        return [nodes.raw("", template.render(
            projects = [c.astext() for c in container.children]
        ), format="html")]
