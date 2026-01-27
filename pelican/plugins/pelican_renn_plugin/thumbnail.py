# Partially based on https://github.com/pelican-plugins/thumbnailer

import logging
import re

from importlib import import_module
from pathlib import Path

pil_imports = None
_LOGGER = logging.getLogger(__name__)


def resize_image(image, resize_spec):
    """
    Resize a given image according to the resize spec.

    :param image: A Pillow image.
    :param resize_spec: Parsed resize spec, a `(w, h, safe)` tuple.
    :return: A new, resized image.
    """

    global pil_imports

    w, h, safe = resize_spec
    crop = False

    # Resize and crop (if safe mode)
    if w == h or (w != "?" and h != "?"):
        # "?x?" is a no-op
        if w == "?":
            return image.copy()
        crop = safe
    # Resize while keeping aspect ratio
    else:
        if w == "?":
            w = image.width
        elif h == "?":
            h = image.height

    w = int(w)
    h = int(h)

    if crop:
        return pil_imports.ImageOps.fit(image, (w, h), pil_imports.Image.BICUBIC)
    elif safe:
        result = image.copy()
        result.thumbnail((w, h), pil_imports.Image.LANCZOS)
        return result
    else:
        return image.resize((w, h), pil_imports.Image.LANCZOS)


def path_to_dict(path):
    """
    Convert a path to a dictionary for `THUMBNAIL_SAVE_AS`.

    :param path: Input path.
    :return: A dictionary of attributes.
    """

    if not isinstance(path, Path):
        path = Path(path)

    return {
        "parts": path.parts,
        "drive": path.drive,
        "root": path.root,
        "anchor": path.anchor,
        "parents": path.parents,
        "parent": path.parent,
        "name": path.name,
        "suffix": path.suffix,
        "suffixes": path.suffixes,
        "stem": path.stem,
    }


def load_pillow(instance):
    """
    Preflight procedure to ensure Pillow is available.

    :param instance: The Pelican instance.
    """

    global pil_imports

    # Don't do anything if the feature is disabled
    if not instance.settings["THUMBNAIL_ENABLE"]:
        return

    if not pil_imports:
        try:
            class PIL:
                Image = import_module(".Image", "PIL")
                ImageOps = import_module(".ImageOps", "PIL")

            pil_imports = PIL
        except ModuleNotFoundError:
            _LOGGER.error("renn: 'THUMBNAIL_ENABLE' is set to True but the PIL package "
                          "was not found.")


def generate_thumbnails(instance):
    """
    A post-process pass that generates thumbnails.

    :param instance: `Pelican` instance.
    """

    global pil_imports

    if not instance.settings["THUMBNAIL_ENABLE"]:
        return
    if not pil_imports:
        _LOGGER.error("renn: 'THUMBNAIL_ENABLE' is set to True but the PIL package "
                      "was not found.")
        return

    save_as = instance.settings["THUMBNAIL_SAVE_AS"]
    skip_existing = instance.settings["THUMBNAIL_SKIP_EXISTING"]
    rspecs = instance.settings["THUMBNAIL_RESIZES"].copy()
    rspec_regex = re.compile(r"^(\d+|\?)(?:([xc])(\d+|\?))?$")

    for resize, resize_spec in rspecs.items():
        w, l, h = rspec_regex.match(resize_spec).groups()

        # safe is set to false for "wch" only
        safe = True
        invalid_values = (None, "?")
        if l == "c" and w not in invalid_values and h not in invalid_values:
            safe = False
        if h is None:
            h = w
        rspecs[resize] = (w, h, safe)

    # Mapping of output_file -> (input_file, resize)
    paths = dict()
    # For every thumbnail path
    for p in instance.settings["THUMBNAIL_PATHS"]:
        thumbnail_path = Path(instance.settings["OUTPUT_PATH"]) / Path(p)
        # We walk the thumbnail path and recursively iterate all files
        for dirpath, _, filenames in thumbnail_path.walk():
            for filename in filenames:
                input_path = dirpath/filename
                # For every resize spec
                for resize, resize_spec in rspecs.items():
                    output_path = Path(save_as.format(
                        resize=resize,
                        resize_spec=resize_spec,
                        **path_to_dict(input_path)
                    ))
                    paths[output_path] = (input_path, resize)

    # Our output files may have been picked by the walk if DELETE_OUTPUT_DIRECTORY is
    # True; we need to remove these invalid input paths if they appear in the output
    # paths
    output_paths = list(paths.keys())
    marked_for_deletion = []
    for output_path, (input_path, _) in list(paths.items()):
        if input_path in output_paths:
            marked_for_deletion.append(output_path)
    for p in marked_for_deletion:
        paths.pop(p)

    # Now we can generate our thumbnails
    for output_path, (input_path, resize) in paths.items():
        if skip_existing and output_path.exists():
            _LOGGER.debug(f"renn: {output_path} already exists, was skipped")
            continue

        # mkdir -p the output directory
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with pil_imports.Image.open(input_path) as image:
                output_image = resize_image(image, rspecs[resize])
                if not output_image:
                    _LOGGER.warning(
                        f"Pillow couldn't resize {input_path} for {resize} spec, saving"
                        f" the original as the thumbnail")
                    output_image = image.copy()
                output_image.save(output_path)
                output_image.close()
                _LOGGER.info(f"renn: {output_path} was created")
        except OSError:
            _LOGGER.error(f"renn: {output_path} couldn't be created")
