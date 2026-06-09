import wikipediaapi

from opencc import OpenCC

cc = OpenCC('s2t')

class WikiSearcher(object):

    def __init__(self) -> None:
        self.wiki = wikipediaapi.Wikipedia(
            user_agent='ChatKG/1.0 (https://github.com/littlewwwhite/KnowledgeGraph-based-on-Raw-text-A27)',
            language='zh'
        )

    def search(self, query):

        result = None

        try:
            page = self.wiki.page(query)

            if not page.exists():
                page = self.wiki.page(cc.convert(query))

            if page.exists():
                result = page

        except Exception as e:
            print(e)

        return result