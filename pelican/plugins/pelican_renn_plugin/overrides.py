import logging
from functools import wraps

from pelican.generators import Generator
from pelican.contents import Page
from pelican.urlwrappers import Category

from .hidden_category import HiddenCategory

_LOGGER = logging.getLogger(__name__)


class BaseOverride:
    """
    Define an override operation. This class must be subclassed, and the `object_type`
    class attribute set.
    """

    # Type of the object that's being written. It must have a `slug` attribute.
    object_type = None

    def __init__(self, obj, generator):
        """
        Initialize the override.

        :param obj: Object that's being written.
        :param generator: A `pelican.generators.Generator` instance, where the context
        resides.

        :raise NotImplementedError: If the `object_type` class attribute is not set by
        the subclass.
        :raise TypeError: If `obj` is not an instance of `object_type`, or if
        `generator` is not an instance of `pelican.generators.Generator`.
        """

        if not self.object_type:
            raise NotImplementedError(f"{self.__class__.__name__} must be subclassed, "
                                      f"and 'cls.object_type' set")
        if not isinstance(obj, self.object_type):
            raise TypeError(f"'obj' should be of type '{self.object_type.__name__}'")
        if not isinstance(generator, Generator):
            raise TypeError(f"'generator' should be of type '{Generator.__name__}'")

        self.object = obj
        self.generator = generator

        # If this is the first time this generator is overridden, backup the original
        # context in the generator itself
        if not hasattr(self.generator, "orig_context"):
            generator.orig_context = generator.context

    @property
    def override_key(self):
        """
        Retrieve the override key used in `OVERRIDES` for the object.

        :return: A tuple like `(object_slug, object_type_name)`.
        """

        return self.object.slug, self.object_type.__name__

    def __call__(self):
        """
        Apply the override to the generator.

        :return: `True` if there was an override for the object, `False` otherwise.
        """

        # Set the context for this page to a copy of the original context
        self.generator.context = self.generator.orig_context.copy()

        # If we have an override for this page, update the temporary context
        override_context = self.generator.settings["OVERRIDES"].get(self.override_key)
        if override_context:
            self.generator.context.update(override_context)
            return True
        return False

    @classmethod
    def restore_context(cls, generator):
        """
        Restore the original context in the generator and delete the temporary
        attribute.

        :param generator: A `pelican.generators.Generator` instance.
        """

        if hasattr(generator, "orig_context"):
            generator.context = generator.orig_context
            delattr(generator, "orig_context")

    @classmethod
    def subclass(cls, obj_type, name=None):
        """
        Declarative creation of a new subclass.

        :param obj_type: A class that has a `slug` attribute.
        :param name: Name for the new class. If `None`, it is computed by appending
        `Override` to `obj_type`'s name.
        :return: A new class.
        """

        if not name:
            name = f"{obj_type.__name__}Override"

        return type(name, (cls,), {"object_type": obj_type})


PageOverride = BaseOverride.subclass(Page)
CategoryOverride = BaseOverride.subclass(Category)


class HiddenCategoryOverride(BaseOverride):
    """
    Override for a hidden category.
    """

    object_type = HiddenCategory

    @property
    def override_key(self):
        # We use the canonical slug instead of the hidden category one
        return self.object.base_category.slug, self.object_type.__name__


def override_page_context(generator, content):
    """
    Signal that overrides the context for the page if required.

    :param generator: A `PagesGenerator` instance.
    :param content: A `Page` object.
    """

    if PageOverride(content, generator)():
        _LOGGER.info(f"renn: An override was found and applied for page {content.slug}")


def restore_page_context(generator, writer):
    """
    When all pages are written, this signal restores the original context.

    :param generator: A `PagesGenerator` instance.
    :param writer: A `Writer` object.
    """

    PageOverride.restore_context(generator)
    _LOGGER.debug(f"renn: Restored the context for {generator}")


def patch_generate_categories(generator):
    """
    Monkey-patch `ArticlesGenerator.generate_categories` to intercept the category
    generation and apply overrides.
    """

    if not generator.settings["OVERRIDES"]:
        return

    @wraps(generator.generate_categories)
    def patched_generate_categories(write):
        category_template = generator.get_template("category")
        for cat, articles in generator.categories:
            override_cls = HiddenCategoryOverride if isinstance(cat, HiddenCategory) \
                else CategoryOverride

            if override_cls(cat, generator)():
                _LOGGER.info(f"renn: An override was found and applied "
                             f"for category {cat.slug}")

            dates = [article for article in generator.dates if article in articles]
            write(
                cat.save_as,
                category_template,
                generator.context,
                url=cat.url,
                category=cat,
                articles=articles,
                dates=dates,
                template_name="category",
                blog=True,
                page_name=cat.page_name,
                all_articles=generator.articles,
            )

        BaseOverride.restore_context(generator)
        _LOGGER.debug(f"renn: Restored the context for {generator}")

    generator.generate_categories = patched_generate_categories
