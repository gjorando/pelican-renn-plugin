from pelican import StaticGenerator
from pelican.plugins.i18n_subsites import i18n_subsites as _i18n_subsites

interlink_static_files = None

def prune_shared_static_files(generator):
    """
    An i18n-subsites patch that addresses an issue with static files sourced with
    `{static}` in a subsite. If `generator` is a `StaticGenerator` from a subsite, it
    will do the following:

    1. remove main static files that are present in the context of the subsite's static
      generator;
    2. remove those files from `StaticGenerator.staticfiles` as well;
    3. call the original `interlink_static_files`.

    The first step makes it so that the `{static}` links in the subsite will properly
    link back to the main static file. The second step prevents Pelican from making an
    extra copy of the main static file in the subsite.

    If `generator` is not a `StaticGenerator`, it only calls the original
    `interlink_static_files`.
    """

    global interlink_static_files

    # We do this only for subsites without a customized STATIC_PATHS
    # Also, we are only concerned with the static generator
    if (not generator.settings["STATIC_PATHS"]
        and isinstance(generator, StaticGenerator)):
        marked_for_deletion = []
        # We fetch the static content from the context
        static_content = generator.context["static_content"]
        # For each main static file
        for static_file in _i18n_subsites._MAIN_STATIC_FILES:
            # If it exists in the subsite static generator
            if (key := static_file.get_relative_source_path()) in static_content:
                # We mark it for deletion in generator.staticfiles
                marked_for_deletion.append(key)
                # We also remove the key from the context
                static_content.pop(key)

        # Finally, we remove these files from generator.staticfiles as well
        for static_file in reversed(generator.staticfiles):
            if static_file.url in marked_for_deletion:
                generator.staticfiles.remove(static_file)

    # Finally, we call the original interlink_static_files to finish processing
    interlink_static_files(generator)


def register():
    """
    Store a backup of the original interlink_static_files, then patch the i18n-subsites
    module, and proceed with the original register function.
    """

    global interlink_static_files
    if not interlink_static_files:
        interlink_static_files = _i18n_subsites.interlink_static_files
    _i18n_subsites.interlink_static_files = prune_shared_static_files

    _i18n_subsites.register()


def __getattr__(name):
    """
    We intercept the module member name resolution so that `interlink_static_files` and
    `register` calls our patched functions, and any other name gets passed to the
    original i18n-subsites plugin.
    """

    match name:
        case "interlink_static_files":
            return prune_shared_static_files
        case "register":
            return register
        case _:
            return getattr(_i18n_subsites, name)
