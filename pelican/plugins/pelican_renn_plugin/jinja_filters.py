import re


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
