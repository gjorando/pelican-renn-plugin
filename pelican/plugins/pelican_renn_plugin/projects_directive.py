import hashlib

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from .jinja_filters import parse_link


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
        project_node = nodes.list_item(classes=["projects-element", "aspect-144/89"])

        # Button tile
        project_node += (button_node := nodes.container(classes=[
            "projects-button"
        ] + "size-full flex items-stretch justify-left "
            "not-pointer-coarse:justify-center group".split(" ")))
        button_node += (button_link_node := nodes.reference(
            refuri=f"#{anchor}",
            classes="flex-1 h-full not-pointer-coarse:opacity-0 duration-1000 "
                    "not-pointer-coarse:bg-link group-hover:opacity-85 flex "
                    "items-center justify-center no-underline".split(" ")
        ))
        button_link_node += (button_title_node := nodes.container(
            classes=["projects-button-title", "text-2xl", "font-bold",
                     "text-foreground", "lg:text-center", "pointer-coarse:m-0.5",
                     "pointer-coarse:text-shadow-lg", "text-shadow-background"]))
        button_title_node += nodes.Text(title)

        # Popup element
        project_node += (popup_node := nodes.container(classes=[
            "projects-popup"
        ] + "invisible z-200 duration-500 opacity-0 target:opacity-100 target:visible "
            "fixed inset-0 bg-background/75 flex items-center "
            "justify-center".split(" "),
                                                       ids=[anchor]))
        popup_node += (popup_window_node := nodes.section(
            classes=["projects-popup-window"]
                    + "w-full overflow-auto max-h-1/2 relative bg-foreground "
                      "text-background p-8 md:w-85/100 lg:w-1/2".split(" ")))
        popup_window_node += (popup_close := nodes.reference(
            refuri="#",
            classes=["projects-popup-close"] +
                    "size-10 text-3xl grid place-items-center font-sans "
                    "no-underline font-black absolute top-4 "
                    "right-4 text-background duration-1000 hover:bg-background "
                    "hover:text-foreground pointer-coarse:bg-background "
                    "pointer-coarse:text-foreground".split(" ")
        ))
        popup_close += nodes.container("", nodes.Text("X"))
        popup_window_node += nodes.title("", nodes.Text(title))
        self.state.nested_parse(self.content, self.content_offset, popup_window_node,
                                match_titles=True)
        if links:
            popup_window_node += nodes.transition(classes=["opacity-50 my-4"])
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
        projects_node = nodes.bullet_list(classes=[
            "projects-modal",
            "floating-block"
        ] + "w-full m-auto grid grid-flow-row grid-cols-2 gap-2 lg:w-1/2 "
            "lg:float-right lg:mx-4".split(" "))
        wrapper_node += projects_node
        self.state.nested_parse(self.content, self.content_offset, projects_node)

        # Move non projects-element items to put them in the wrapper
        # We iterate in reverse as to not break the iteration if a child is removed
        for child in reversed(projects_node.children):
            if not isinstance(child, nodes.list_item):
                projects_node.remove(child)
                child["classes"].append("mb-4")
                wrapper_node += child

        return [wrapper_node]
