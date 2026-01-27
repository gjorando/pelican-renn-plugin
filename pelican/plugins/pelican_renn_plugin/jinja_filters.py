import re

from pathlib import Path

from jinja2 import pass_context

from .thumbnail import path_to_dict


def register_filters(generator):
    """
    Signal that registers the custom jinja filters.
    """

    generator.env.filters["parse_link"] = parse_link
    generator.env.filters["get_flag_emoji"] = get_flag_emoji
    generator.env.filters["get_thumbnail"] = get_thumbnail


def parse_link(raw):
    """
    Parse a raw link (`text <uri>` or `uri`).

    :param raw: Raw URI string.
    :return: A `(title, uri)` tuple.
    """

    match = re.match(r"^(.*)\s*<([^>]+)>$", raw)
    if not match:
        return raw, ""
    uri = match[2]
    title = match[1] if match[1] else match[2]
    return title.strip(), uri.strip()


def get_flag_emoji(code):
    """
    Retrieve a flag emoji from a country code.

    :param env: `jinja2.Environment` object.
    :param code: 2-character country code.
    :return: A flag emoji character.
    """

    if code == "en":
        code = "gb"

    return "".join([chr(127397 + ord(c)) for c in list(code.upper())])


@pass_context
def get_thumbnail(ctx, path, resize):
    """
    Retrieve the path of a thumbnail for a given image.

    :param ctx: Jinja `Context`.
    :param path: Path of the image.
    :param resize: Name of the resize spec in `THUMBNAIL_RESIZES`.
    :return: The thumbnail path, or the original path if the thumbnail doesn't exist.
    """

    resize_spec = ctx.get("THUMBNAIL_RESIZES")
    if not resize_spec:
        return path

    return ctx["THUMBNAIL_SAVE_AS"].format(
        resize=resize,
        resize_spec=resize_spec,
        **path_to_dict(path)
    )
