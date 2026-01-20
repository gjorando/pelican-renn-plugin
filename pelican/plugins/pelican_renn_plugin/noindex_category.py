from functools import wraps
import os


def patch_generate_direct_templates(generator):
    """
    Monkey-patch `ArticlesGenerator.generate_direct_templates` to intercept the index
    generation and remove articles in no-index categories.
    """

    if not generator.settings["NOINDEX_CATEGORIES"]:
        return

    @wraps(generator.generate_direct_templates)
    def patched_generate_direct_templates(write):
        for template in generator.settings["DIRECT_TEMPLATES"]:
            save_as = generator.settings.get(
                f"{template.upper()}_SAVE_AS", f"{template}.html"
            )
            url = generator.settings.get(f"{template.upper()}_URL", f"{template}.html")
            if not save_as:
                continue

            match template:
                case "index":
                    def _process(l):
                        return [a for a in l
                                if a.category.slug
                                   not in generator.settings["NOINDEX_CATEGORIES"]]

                    articles = _process(generator.articles)
                    dates = _process(generator.dates)
                case _:
                    articles = generator.articles
                    dates = generator.dates

            write(
                save_as,
                generator.get_template(template),
                generator.context,
                articles=articles,
                dates=dates,
                blog=True,
                template_name=template,
                page_name=os.path.splitext(save_as)[0],
                url=url,
            )

    generator.generate_direct_templates = patched_generate_direct_templates
