# Based on the original Tailwind CSS plugin for Pelican https://github.com/pelican-plugins/tailwindcss/

import os
import logging

from importlib import import_module
from pathlib import Path

pytailwindcss = None
_LOGGER = logging.getLogger(__name__)


def compile_css_file(input_file, tw_config, version, instance):
    """
    Compile a single CSS file and put it in its output directory

    :param input_file: Path to the input CSS file.
    :param tw_config: Tailwind CSS configuration file.
    :param version: Tailwind CSS version to use.
    :param instance: Pelican instance.
    """

    global pytailwindcss

    # For each static path (content and theme static path), compute the destination
    static_paths = [
        (
            Path(instance.path)/static_path,
            Path(instance.output_path)/static_path
        )
        for static_path in instance.settings["STATIC_PATHS"]
    ] + [
        (
            Path(instance.theme)/static_path,
            Path(instance.output_path)/instance.settings["THEME_STATIC_DIR"]
        )
        for static_path in instance.settings["THEME_STATIC_PATHS"]
    ]

    # Find the static path associated to the input file
    for static_path, output_dir in static_paths:
        # If found, resolve the output path and run Tailwind CSS CLI
        if input_file.resolve().is_relative_to(static_path):
            output_path = output_dir/input_file.resolve().relative_to(static_path)
            command = f"-i {input_file} -o {output_path} " \
                      f"{f"-c {tw_config}" if tw_config else ""} " \
                      f"{"--minify" if instance.settings["TAILWINDCSS_MINIFY"] else ""}"
            _LOGGER.info(f"renn: Compiling {input_file} into {output_path}")
            _LOGGER.debug(f"Running `{command}`")
            process = pytailwindcss.run(
                command,
                env=os.environ.copy(),
                cwd=os.getcwd(),
                live_output=True,
                version=version
            )
            if process.returncode != 0:
                _LOGGER.error(f"renn: Tailwind CSS CLI returned a non-zero exit code "
                              f"({process.returncode})")
    else:
        # Usually not an issue: with i18n-subsites, translated websites cross-link
        # static files, so this is totally expected
        _LOGGER.info(f"renn: {input_file} Tailwind CSS compilation skipped")


def resolve_tailwind_version(version):
    """
    Resolve the "latest" version of the Tailwind CLI to the actual version tag.

    :param version: Version string.
    :return: `version` if != "latest", otherwise the latest version tag.
    """

    # No-op if version is not "latest"
    if version != "latest":
        return version

    # Retrieve the latest tag from the GitHub API
    return import_module("requests").get(
        "https://api.github.com/repos/tailwindlabs/tailwindcss/tags"
    ).json()[0]["name"]


def pytailwindcss_module():
    """
    Fetch the `pytailwindcss` module and import it if necessary.

    :return: The `pytailwindcss` Python module, or `None` if the module couldn't be
    loaded.
    """

    global pytailwindcss

    # Try to import the pytailwindcss module
    if not pytailwindcss:
        try:
            pytailwindcss = import_module("pytailwindcss")
        except ModuleNotFoundError:
            _LOGGER.error("renn: 'TAILWINDCSS_ENABLE' is set to True but the "
                          "pytailwindcss module was not found.")

    return pytailwindcss


def load_tailwind(instance):
    """
    Preflight procedure to ensure Tailwind CLI is available, and install it if needed.

    :param instance: The Pelican instance.
    """

    # Don't do anything if Tailwind is disabled or not available
    if not (instance.settings["TAILWINDCSS_ENABLE"]
            and (twcss := pytailwindcss_module())):
        return

    # If needed, install the required version
    version = resolve_tailwind_version(instance.settings["TAILWINDCSS_VERSION"])
    if not twcss.utils.get_bin_path(version).exists():
        _LOGGER.warning(f"renn: Tailwind CSS CLI {version} will be downloaded")
        twcss.install(version)
    _LOGGER.info(f"renn: Using Tailwind CSS CLI {version}")


def compile_css(instance):
    """
    When Pelican is done writing the output directory, this post-process pass compiles
    the Tailwind CSS files and copy them at the correct output location.

    :param instance: The Pelican instance.
    """

    # Don't do anything if Tailwind is disabled or not available
    if not (instance.settings["TAILWINDCSS_ENABLE"]
            and (twcss := pytailwindcss_module())):
        return

    version = resolve_tailwind_version(instance.settings["TAILWINDCSS_VERSION"])
    _LOGGER.info(f"renn: Compiling CSS using Tailwind CSS CLI {version}")

    tw_config = Path(instance.settings["TAILWINDCSS_CONFIG"]) \
        if instance.settings["TAILWINDCSS_CONFIG"] else None
    if tw_config:
        # Don't do anything if the configuration file doesn't exist
        if not tw_config.exists():
            _LOGGER.error(f"renn: '{tw_config}' not found")
            return
        _LOGGER.info(f"renn: Using Tailwind CSS config file '{tw_config}'")

    # Compile each Tailwind CSS input file
    for input_file in instance.settings["TAILWINDCSS_INPUT_FILES"]:
        input_file = Path(input_file)
        if not input_file.exists():
            _LOGGER.error(f"renn: {input_file} not found")
            continue
        compile_css_file(input_file, tw_config, version, instance)
