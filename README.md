# pelican-renn: A Plugin for Pelican

A plugin for my own needs. It is designed to be tightly integrated to a custom theme I made, [`pelican-renn`](https://github.com/gjorando/pelican-renn).

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

A `projects`directive is a grid of project tiles with a pop-up element.

Example usage:

```rest
.. projects::

    .. project::
        :title: My project
        :image: images/my_project.jpg
        :links: Website <https://perdu.com>, http://other-link.net

        This is a description for my project.

    .. project::
        :title: My other project
        :image: images/my_other_project.jpg

        This is a description for my other project.

    This is arbitrary content that goes alongside the project grid. It will always be inserted after it.

    Another paragraph!
```

#### `projects`

* _Directive Type:_ `projects`
* _Directive Arguments:_ n.a.
* _Directive Options:_ n.a.
* _Directive Content:_ one or more `project` directives (one per project tile), and arbitrary content that accompanies the project grid.

#### `project`

* _Directive Type:_ `project`
* _Directive Arguments:_ n.a.
* _Directive Options:_
  * `title`: name of the project (mandatory)
  * `image`: background image for the tile (mandatory)
  * `links`: optional list of links added in the pop-up (optional, see example below).
* _Directive Content:_ the content of the pop-up.

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
