# Partially based on https://github.com/pelican-plugins/thumbnailer

import logging

from importlib import import_module
from pathlib import Path

pil_imports = None
_LOGGER = logging.getLogger(__name__)


class ResizeSpec:
    """
    An object describing a resizing operation. A `ResizeSpec` instance can be called to
    perform the operation.
    """

    def __init__(self, spec_format):
        """
        :param spec_format: See `README.md` for more information.
        :raise ValueError: If `spec_format`'s value is incorrect.
        :raise TypeError: If `spec_format` is not a tuple, integer or callable.
        :raise RuntimeError: If the spec_format is not a callable while Pillow is not
        installed.
        """

        self.w = None
        self.h = None
        self.keep_aspect = False
        self.custom_callback = None

        # A single integer is equivalent to (s,)
        if isinstance(spec_format, int):
            spec_format = (spec_format,)

        # Parse the raw spec format
        match spec_format:
            case (int(s),):  # sxs
                self.w = self.h = int(s)
            case (int(s), bool(c)):  # sxs or scs
                self.w = self.h = s
                self.keep_aspect = c
            case (w, h) if ((w is None or isinstance(w, int)) and
                            (h is None or isinstance(h, int))):  # wxh
                self.w = w
                self.h = h
            case (w, h, bool(c)) if ((w is None or isinstance(w, int)) and
                                     (h is None or isinstance(h, int))):  # wxh or wch
                self.w = w
                self.h = h
                self.keep_aspect = c
            case f if callable(f):  # Custom resize operation
                self.custom_callback = f
            case _:
                if isinstance(spec_format, tuple):
                    raise ValueError(f"{spec_format}: incorrect spec format")
                raise TypeError(f"{type(spec_format)}: not a valid spec format type")

        # If a dimension is set, it must be strictly positive
        if (self.w is not None and self.w <= 0) or \
           (self.h is not None and self.h <= 0):
            raise ValueError("Dimensions should be strictly positive integers")

        # If we don't have a custom callback, Pillow is a hard requirement
        if not (self.custom_callback or pil_imports):
            raise RuntimeError("Pillow is not installed")

    def __call__(self, image):
        """
        Perform the resize operation.

        :param image: A Pillow image.
        :return: A new, resized image.
        """

        # If we have a custom callback, it is used instead
        if self.custom_callback:
            return self.custom_callback(image)

        # Operations where the image is not deformed
        if self.keep_aspect:
            # We crop if both dimensions are set
            if self.w and self.h:
                result = pil_imports.ImageOps.fit(
                    image, (self.w, self.h), pil_imports.Image.BICUBIC)
            # Otherwise, it is a thumbnail resizing
            else:
                result = image.copy()
                result.thumbnail((self.w or image.width, self.h or image.height),
                                 pil_imports.Image.LANCZOS)
        # Operation where the image is deformed
        else:
            result = image.resize((self.w or image.width, self.h or image.height),
                                  pil_imports.Image.LANCZOS)

        return result

    def __str__(self):
        """
        Create the resize_spec string. See `README.md` for more information.

        :return: The resize spec string.
        """

        # If we have a custom callback, use its name or representation
        if self.custom_callback:
            return getattr(self.custom_callback, "__name__", repr(self.custom_callback))

        return (f"{self.w if self.w else "?"}"
                f"{"c" if self.keep_aspect else "x"}"
                f"{self.h if self.h else "?"}")


def path_to_dict(path):
    """
    Convert a path to a dictionary for `THUMBNAIL_SAVE_AS`. This dictionary holds all
    the common attributes of a `pathlib.Path` object.

    :param path: Input path.
    :return: A dictionary of attributes, namely: parts, drive, root, anchor, parents,
    parent, name, suffix, suffixes and stem.
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
    Preflight procedure to ensure Pillow is available and import it, only if the
    thumbnail feature is enabled.

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


def _parse_output_path(input_path, save_as, resize, resize_spec):
    """
    Small subroutine to parse the output path.

    :param input_path: Image input path.
    :param save_as: The THUMBNAIL_SAVE_AS format string.
    :param resize: Name of the resize spec.
    :param resize_spec: `ResizeSpec` object.
    :return: Formated output path;
    """

    return Path(save_as.format(
        resize=resize,
        resize_spec=str(resize_spec),
        **path_to_dict(input_path)
    ))


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
    # Get our ResizeSpec instances
    rspecs = {name: ResizeSpec(spec) for name, spec
              in instance.settings["THUMBNAIL_RESIZES"].items()}

    # We associate each output file to be generated with its input file and resize spec
    paths = dict()  # {output_path: (input_path, resize_name)}
    # For every resize spec
    for resize, resize_spec in rspecs.items():
        # For every thumbnail path
        for p in instance.settings["THUMBNAIL_PATHS"]:
            thumbnail_path = Path(instance.settings["OUTPUT_PATH"]) / Path(p)

            # If the path is actually a single file
            if thumbnail_path.is_file():
                # We just add it to our list of paths
                output_path = _parse_output_path(thumbnail_path, save_as, resize,
                                                 resize_spec)
                paths[output_path] = (thumbnail_path, resize)
                continue

            # Otherwise we walk the thumbnail path and recursively iterate all files
            for dirpath, _, filenames in thumbnail_path.walk():
                for filename in filenames:
                    input_path = dirpath/filename
                    output_path = _parse_output_path(input_path, save_as, resize,
                                                     resize_spec)
                    paths[output_path] = (input_path, resize)

    # Our output files may have been picked by the walk if DELETE_OUTPUT_DIRECTORY is
    # False; we need to remove these invalid input paths if they appear in the output
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

        # At long last, we can actually resize our image!
        try:
            with pil_imports.Image.open(input_path) as image:
                output_image = rspecs[resize](image)
                # Safeguard: if for some reason output_image is None, we log the error
                if not output_image:
                    _LOGGER.error(f"renn: {output_path} couldn't be created")
                    continue
                output_image.save(output_path)
                output_image.close()
                _LOGGER.info(f"renn: {output_path} was created")
        except OSError:
            # If for some reason we couldn't open the image, we log the error
            _LOGGER.error(f"renn: {input_path} couldn't be opened")
