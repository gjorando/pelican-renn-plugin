# pelican-renn: A Plugin for Pelican

A plugin for my own needs. It is designed to be tightly integrated to a custom theme I made, [`pelican-renn`](https://github.com/gjorando/pelican-renn). See over there for an example configuration file.

## Installation

Using git submodules:

```bash
# In the project root
git submodule add git@github.com:gjorando/pelican-renn-plugin.git plugin
```

Then add the following to `pelicanconf.py`:

```python
# Plugins
PLUGIN_PATHS = ["plugin/pelican/plugins/"]
PLUGINS = ["pelican_renn_plugin", "..."]
```

## Usage

### The `projects` and `project` directives

A `projects` directive is a list of projects. The default templates effectively render this as a list (`<ul>`) of `popover` elements with their associated `button` element. Each button is rendered as a tile with a background image, but feel free to override the templates to render the directives anyway you want.

Example usage:

```rest
.. projects::

    .. project:: My project
        :image: images/my_project.jpg
        :links: Website <https://perdu.com>, http://other-link.net

        This is a description for my project.

    .. project:: My other project
        :image: images/my_other_project.jpg

        This is a description for my other project.

    This is arbitrary content that goes alongside the project grid. It will always be inserted after it.

    Another paragraph!
```

#### `projects`

* _Directive Type:_ `projects`
* _Directive Arguments:_ n.a.
* _Directive Options:_
  * `template`: override for the default rendering template (optional, see below)
* _Directive Content:_ one or more `project` directives (one per project tile), and arbitrary content that accompanies the project grid

The template context includes the following additional values.

* `projects`: rendered `project` elements (`list`)
* `wrapped`: rendered arbitrary content that accompanies the project grid (`list`)

#### `project`

* _Directive Type:_ `project`
* _Directive Arguments:_ one, required (project name)
* _Directive Options:_
  * `image`: background image for the button (required)
  * `links`: optional list of links added in the pop-up (optional, see example above)
  * `template`: override for the default rendering template (optional, see below)
* _Directive Content:_ the content of the pop-up

The template context includes the following additional values.

* `project_title`: project name (`str`)
* `project_image`: image URI (`str`)
* `project_links`: links (`list` of `tuple` as `(title, uri)`)
* `project_content`: rendered content of the directive (`str`)
* `popover_id`: a unique identifier for the project (`str`)

### Hidden categories

This plugin implements "virtual" categories for each "base" category with at least one hidden article. We call this hidden category a "virtual" category, because it is not listed in the category list page. It is merely a view of the base category which includes articles with a status set to `hidden` or `published`. A number of settings can be set within `pelicanconf.py`.

#### `HIDDENCATEGORY_ENABLE`

A flag that enables the feature. The default is `False`.

#### `HIDDENCATEGORY_NAME`

The name of the virtual category. `base_category` is available as a template parameter to expose the base category object. The default is `{base_category}-full` (the string representation of `Category` objects is the category name).

#### `HIDDENCATEGORY_URL`

The URL to use for a virtual category. The default is computed from `CATEGORY_URL`, adding `-full` to the last folder.

#### `HIDDENCATEGORY_SAVE_AS`

The location to save a virtual category. The default is computed from `HIDDENCATEGORY_URL`, adding an `index.html` if
the URL doesn't specify a filename.

#### `HIDDENCATEGORY_OVERRIDES`

Dictionary mapping a base category slug to a dictionary of setting overrides. These overrides update the `settings` attribute of a category, while leaving the original settings untouched. The default is `{}`.

#### `HIDDENCATEGORY_EXCLUDES`

List of category slugs to ignore in the creation of the hidden categories. The default is `[]`.

### No-index categories

This plugin also enables the capability to remove certain categories from the `index` page. This doesn't mean that the articles are hidden in any way, though. They are still listed in the per-category, per-author and per-tag pages, and in the archives. Moreover, the category remains visible in the `categories` page.

#### `NOINDEX_CATEGORIES`

List of categories whose articles will be removed from the index. The default is `[]`.

### Tailwind CSS integration

Taking inspiration from an older [Pelican plugin](https://github.com/pelican-plugins/tailwindcss/), this plugin offers a [Tailwind CSS](https://tailwindcss.com) integration using [`pytailwindcss`](https://pypi.org/project/pytailwindcss/).

#### `TAILWINDCSS_ENABLE`

A flag that enables the feature. The default is `False`.

#### `TAILWINDCSS_VERSION`

Tailwind CSS version to use. The default is `latest`.

#### `TAILWINDCSS_CONFIG`

Optional Tailwind CSS configuration file, relative to the current working directory. The default is `None`, as this has been deprecated since Tailwind CSS 4.x.

#### `TAILWINDCSS_INPUT_FILES`

List of Tailwind CSS input files, relative to the current working directory. All of these files should be contained in any path of either `STATIC_PATHS` or `THEME_STATIC_PATHS`. The default is `[]`.

#### `TAILWINDCSS_MINIFY`

Whether to minify the output files. The default is `True`.

### Thumbnails

Taking inspiration from an older [Pelican plugin](https://github.com/pelican-plugins/thumbnailer/), this plugin allows for automatic creation of thumbnail images.

#### `THUMBNAIL_ENABLE`

A flag that enables the feature. The default is `False`.

#### `THUMBNAIL_SAVE_AS`

The location to save a thumbnail. The available format variables correspond to the majority of `pathlib.Path`'s common attributes for the path of the original image. `resize` and `resize_spec` are also available, exposing the name and spec of the resize operation (see `THUMBNAIL_RESIZES`). The default is `{parent}/thumbnails/{stem}_{resize}{suffix}` (for a given image, put its thumbnail in a thumbnails subdirectory of the original image's directory, and add `_{resize}` to its file name, before the extension).

#### `THUMBNAIL_PATHS`

Paths to consider for thumbnail generation. The default is `["images"]`.

#### `THUMBNAIL_RESIZES`

Resize operations to apply to each image. The key gives the operation a name, while the value can be of any of the following formats, where `w`, `h`, `s` are positive integer values:

* `wxh` resizes to exactly wxh pixels, cropping if necessary;
* `wch` resizes to exactly wxh pixels, deforming the image in the process;
* `wx?` and `?xh` resize to the specified width/height while keeping the original aspect ratio;
* `s` is a shorthand for `wxh`, with `w=h=s`.

The default is `{"square": "150", "wide": "150x?", "tall": "?x150"}`.

#### `THUMBNAIL_SKIP_EXISTING`

Whether to skip a thumbnail if it already exists in the output path. The default is `True`.

### HTML5 reStructuredText parser

This plugin automatically enables HTML5 parsing of reST files. This feature is enabled by default.

#### `HTML5_ENABLE`

Whether to generate HTML5 output from reST files. The default is `True`.
