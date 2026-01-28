import logging

from collections import defaultdict
from operator import attrgetter

from pelican.contents import Category

_LOGGER = logging.getLogger(__name__)

class HiddenCategory(Category):
    """
    Virtual categories that are meant to list all the articles from the base category,
    including hidden articles. Note that all articles retain their original category,
    hence why we call them "virtual" categories.
    """

    def __init__(self, base_category):
        # Parse the name of the hidden category
        name = base_category.settings[f"{self.__class__.__name__.upper()}_NAME"]

        super().__init__(name.format(base_category=base_category),
                         base_category.settings)

        # The base category is stored here
        self.base_category = base_category


def create_hidden_categories(generator):
    """
    Signal that creates our hidden categories.

    :param generator: Generator instance.
    """

    # Do nothing if the functionality is not enable
    if not generator.settings["HIDDENCATEGORY_ENABLE"]:
        return

    extra_categories = defaultdict(list)
    for article in generator.hidden_articles:
        category_name = article.category.name if article.category else None
        # Skip articles without a category, or excluded categories
        if (not category_name
            or article.category.slug in generator.settings["HIDDENCATEGORY_EXCLUDES"]):
            continue

        extra_categories[category_name].append(article)

    # We also add the visible articles
    for article in generator.articles:
        category_name = article.category.name if article.category else None
        # Skip articles without a category
        if not category_name:
            continue

        # Categories that don't have hidden articles won't generate a hidden category
        if category_name in extra_categories:
            extra_categories[category_name].append(article)

    # We copy the original list because we want it to be distinct from
    # generator.context["categories"], which keeps the new category hidden from the
    # categories template page
    generator.categories = generator.categories.copy()
    for category_name, articles in extra_categories.items():
        category = HiddenCategory(articles[0].category)
        _LOGGER.info(f"renn: Generating hidden category {category} for "
                     f"base category {articles[0].category}")
        articles.sort(key=attrgetter("date"), reverse=True)
        generator.categories.append((category, articles))
