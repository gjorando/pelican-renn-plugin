import re
import hashlib

from docutils import nodes
from docutils.parsers.rst import Directive, directives


def parse_link(raw):
    """
    Small function that parses a raw link (`text <uri>` or `uri`).
    """

    match = re.match(r"^(.*)\s*<([^>]+)>$", raw)
    if not match:
        return raw, ""
    uri = match[2]
    title = match[1] if match[1] else match[2]
    return title.strip(), uri.strip()


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

        # Ensure we are inside a projects-modal
        if not "projects-modal" in self.state.parent["classes"]:
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

        # Overall element
        project_node = nodes.list_item(classes=["projects-element"])

        # Button tile
        project_node += (button_node := nodes.container(classes=["projects-button"]))
        button_node += (button_link_node := nodes.reference(refuri=f"#{anchor}"))
        button_link_node += (button_title_node := nodes.container(
            classes=["projects-button-title"]))
        button_title_node += nodes.Text(title)

        # Popup element
        project_node += (popup_node := nodes.container(classes=["projects-popup"],
                                                       ids=[anchor]))
        popup_node += (popup_window_node := nodes.section(
            classes=["projects-popup-window"]))
        popup_window_node += nodes.reference(text="\xD7", refuri="#",
                                             classes=["projects-popup-close"])
        popup_window_node += nodes.title("", nodes.Text(title))
        self.state.nested_parse(self.content, self.content_offset, popup_window_node,
                                match_titles=True)
        if links:
            popup_window_node += nodes.transition()
            popup_window_node += (links_node := nodes.bullet_list())
            for link_text, link_uri in links:
                links_node += nodes.list_item(
                    "",
                    nodes.reference(text=link_text, refuri=link_uri)
                )

        # Dynamic button background styling
        class_name = f"projects-bg-{hashlib.md5(image.encode()).hexdigest()[:8]}"
        button_node["classes"].append(class_name)
        style_node = nodes.raw(
            "",
            f"""
            <style>
                .{class_name} {{
                    background: center/contain no-repeat url("/{image}");
                }}
            </style>
            """,
            format="html"
        )

        return [style_node, project_node]


class ProjectsDirective(Directive):
    """
    A directive that creates a project list modal.
    """

    has_content = True

    def run(self):
        """
        Create a bullet list node and populate it with the contents of the directive.
        """

        wrapper_node = nodes.container(classes=["float-wrapper"])
        projects_node = nodes.bullet_list(classes=["projects-modal", "floating-block"])
        wrapper_node += projects_node
        self.state.nested_parse(self.content, self.content_offset, projects_node)

        # Move non projects-element items to put them in the wrapper
        # We iterate in reverse as to not break the iteration if a child is removed
        for child in reversed(projects_node.children):
            if not isinstance(child, nodes.list_item):
                projects_node.remove(child)
                wrapper_node += child

        return [wrapper_node]
