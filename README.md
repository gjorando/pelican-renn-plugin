# pelican-renn: A Plugin for Pelican

A plugin for my own needs

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

### The "projects" reST directive

A grid of project tiles with a pop-up element.

* _Directive Type:_ "projects"
* _Directive Arguments:_ n.a.
* _Directive Options:_ n.a.
* _Directive Content:_ one or more "project" directives (one per project tile), and arbitrary content that accompanies the project grid.

Example usage:

```rest
.. project::

    (One or more "project" directives, see below)

    This is arbitrary content that goes alongside the project grid. It will always be inserted after it.

    Another paragraph!
```

### The "project" reST directive

A single element of the "projects" grid.

* _Directive Type:_ "project"
* _Directive Arguments:_ n.a.
* _Directive Options:_
  * _"title":_ name of the project (mandatory)
  * _"image":_ background image for the tile (mandatory)
  * _"links":_ optional list of links added in the pop-up (optional, see example below).
* _Directive Content:_ the content of the pop-up.

Example usage:

```rest
.. project::
    :title: My project
    :image: images/my_project.jpg
    :links: Website <https://perdu.com>, http://other-link.net

    This is a description for my project.
```
