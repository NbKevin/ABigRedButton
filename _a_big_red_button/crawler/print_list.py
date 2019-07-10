"""
This script implements utilities to parse and manage a print page
from Web of Science.

Kevin Ni, kevin.ni@nyu.edu.
"""

from typing import *
from lxml import etree
from _a_big_red_button.support.configuration import get_config
from _a_big_red_button.support.log import get_logger
from _a_big_red_button.crawler.article_attribute_parser import *

# get logger
logger = get_logger('crawler')

# get config
config = get_config('crawler')


class WoKDOIArticle:
    @staticmethod
    def make_empty():
        return WoKDOIArticle('', '',
                             2100,
                             None, '', None, None)

    def __init__(self,
                 journal: str,
                 first_author: str,
                 year: Union[int, str],
                 page: Optional[Union[int, str]],
                 doi: str,
                 volume: Optional[Union[int, str]] = None,
                 issue: Optional[Union[int, str]] = None):
        self.journal = journal
        self.volume, self.issue = volume, issue
        self.page = page
        self.doi = doi
        self.first_author = first_author
        self.year = year

    # noinspection PyUnresolvedReferences
    def parse(self):
        self.doi = self.doi.strip('DOI\n ')
        if self.page is not None:
            self.page = int(self.page.lstrip('pP[').split('-')[0])
        if self.volume is not None:
            self.volume = self.volume.lstrip('vV[').split('-')[0]
        if self.issue is not None:
            self.issue = int(self.issue)
        if isinstance(self.year, str):
            if len(self.year) == 4:
                self.year = int(self.year)
            else:
                self.year = int(self.year.split()[-1])

    def __repr__(self):
        return f'Article(author={self.first_author}, journal={self.journal},' \
            f'doi={self.doi})'


class WoKPrintArticle:
    # load name map
    NAME_MAP: Dict[str, str] = config.name_map.dict.copy()

    class PrimitiveAttributePair:
        def __init__(self, name: str, value: List[str]):
            self.name: str = name
            self.value: Union[WoKDOIArticle, str, List[str], int] = value
            self.clean_up_name()
            self.clean_up_value()
            self.parse_value()

        def __repr__(self):
            return f'{self.name} = {self.value}'

        __str__ = __repr__

        def clean_up_name(self):
            self.name = self.name[:-1]

        def clean_up_value(self):
            if isinstance(self.value[0], str):
                # xpath text()
                new_value = map(
                    lambda text: text.strip(),
                    filter(
                        lambda text: text != '\n\n',
                        filter(
                            lambda text: text != '\n',
                            self.value)
                    )
                )
                self.value = list(new_value)
            else:
                # value tag
                self.value = list(
                    filter(lambda text: text,
                           map(lambda element: element.text, self.value)))

        def parse_value(self):
            if len(self.value) == 1:
                self.value = self.value[0]

                if self.name == '作者' or self.name == '作者关键词' or \
                        self.name == 'Keywords Plus':
                    self.value = split_by()(self.value)
                else:
                    try:
                        self.value = as_int(self.value)
                    except ValueError:
                        pass  # if this is not a valid int then let it be
            elif self.name == '引用的参考文献':
                citations = []
                for citation in self.value:
                    fields = ['first_author', 'year', 'journal']
                    values = citation.replace('\n', '').split(', ')
                    if not any(filter(lambda value: value.startswith('DOI'), values)):
                        continue
                    as_doi = WoKDOIArticle.make_empty()
                    bad_citation = False
                    for i in range(3):
                        setattr(as_doi, fields[i], values[i])
                        if as_doi.first_author.isnumeric():
                            logger.warning(f'citation [{citation}] has no author, discarded')
                            bad_citation = True
                            break
                    if bad_citation:
                        continue
                    for value in values[3:]:
                        if value.startswith('V'):
                            setattr(as_doi, 'volume', value)
                        elif value.startswith('P'):
                            setattr(as_doi, 'page', value)
                        elif value.startswith('DOI'):
                            setattr(as_doi, 'doi', value)
                    if not as_doi.doi:
                        continue
                    as_doi.parse()
                    citations.append(as_doi)
                self.value = citations
            else:
                pass
                self.value = self.value  # obviously IntelliJ has a bug here

    def __init__(self, source: etree.ElementBase):
        self.source = source
        self.attributes = list(self.find_all_attributes())

    def has_attributes(self, attribute: str):
        try:
            _ = getattr(self, attribute)
            return True
        except ValueError:
            return False

    def __getattr__(self, name):
        # map ascii attributes names to actual fields
        if name in self.NAME_MAP:
            mapped_name = self.NAME_MAP[name]
            for attribute in self.attributes:
                if mapped_name == attribute.name:
                    return attribute.value
            if mapped_name in self.NAME_MAP:
                return self.__getattr__(mapped_name)
            raise ValueError(f'Field [{name}] is recorded in the name map, '
                             f'however its mapped name [{mapped_name}] is not found '
                             f'in the available attributes')
        raise ValueError(f'Unknown field [{name}]')

    def find_all_attributes(self):
        for td in self.source.findall('tr/td'):
            for title in td.findall('b'):
                if title is None:
                    continue

                if not title.text.endswith(':'):
                    continue

                value = title.xpath('following-sibling::value[1]/text()')
                if value:
                    yield self.PrimitiveAttributePair(title.text, value)
                    continue

                text = td.xpath('text()')
                if text:
                    yield self.PrimitiveAttributePair(title.text, text)

    def __repr__(self):
        return f'Article(title={self.title[:36]}(...), doi={self.doi})'

    def __str__(self):
        return f'Article(title={self.title[:36]}(...), doi={self.doi})'


class WoKPrintList:
    def __init__(self, source: 'TextIO'):
        self.source = source
        self.root = etree.parse(self.source, etree.HTMLParser(recover=True, encoding='UTF-8'))

    def __repr__(self):
        return "WokPrintList()"

    def find_all_articles(self, year_range: Optional[range] = None):
        count = 0
        for table in self.root.xpath('//form[@id="printForm"]/table[not(@cellpadding)]'):
            count += 1
            try:
                article = WoKPrintArticle(table)
                if not article.has_attributes('doi'):
                    logger.warning(f'article(name={article.title}) has no DOI, discarded')
                    continue
                print(article)
                if year_range is not None:
                    # try parse the year
                    year = article.year
                    if isinstance(year, int):
                        if year in year_range:
                            yield article
                        else:
                            logger.info(f"{article} discarded, year not match")
                    else:
                        year = year.split()[-1]
                        if year.isdigit():
                            if float(year) in year_range:
                                yield article
                            else:
                                logger.info(f"{article} discarded, year not match")
                        else:
                            logger.info(f"{article} discarded, no year provided")
                else:
                    yield article
            except Exception as e:
                logger.warning('cannot parse this specific article, skipped')
                logger.debug(f"exception says: {e}")
                logger.debug(f'also says: this is article {count} in this print list')

        if count == 0:
            logger.warning(f"{self} no articles found, this print list may be broken")
