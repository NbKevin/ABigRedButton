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


def normalize_name_abbr(name: str):
    return name.strip().replace(',', '').replace('.', '').upper()


class WoKCitation:
    @staticmethod
    def make_empty():
        return WoKCitation('', '',
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

    def as_export_dict(self):
        export_names = config.export_names.citation.copy()
        export_dict = dict()
        for name in export_names:
            try:
                export_dict[name] = getattr(self, name)
            except AttributeError:
                logger.error(f"citation has no such field [{name}]")
                return None
        return export_dict


class WoKPrintArticle:
    # load name map
    NAME_MAP: Dict[str, str] = config.name_map.dict.copy()

    class PrimitiveAttributePair:
        def __init__(self, name: str, value: List[str]):
            self.name: str = name
            self.value: Union[WoKCitation, str, List[str], int] = value
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

                if self.name == '作者' or self.name == '作者关键词':
                    self.value = split_by()(self.value)
                    if self.name == '作者':
                        new_authors = []
                        for raw_author in self.value:
                            abbr, full = raw_author[:-1].split('(')
                            new_authors.append(
                                {'abbr': normalize_name_abbr(abbr.strip()),
                                 'full': full.strip()})
                        self.value = new_authors
                elif self.name in ('研究方向', '电子邮件地址', 'KeyWords Plus', 'Web of Science 类别'):
                    self.value = list(map(lambda s: s.strip(), split_by(';')(self.value)))
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
                    as_doi = WoKCitation.make_empty()
                    bad_citation = False
                    for i in range(3):
                        setattr(as_doi, fields[i], values[i])
                        if as_doi.first_author.isnumeric():
                            logger.warning(f'citation [{citation}] has no author, discarded')
                            bad_citation = True
                            break
                    as_doi.first_author = normalize_name_abbr(as_doi.first_author)
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

    def as_export_dict(self):
        export_names = sorted(config.export_names.article.copy())
        export_dict = dict()
        for name in export_names:
            try:
                value = getattr(self, name)
                if isinstance(value, WoKCitation):
                    export_dict[name] = value.as_export_dict()
                elif isinstance(value, List):
                    export_dict[name] = list(
                        map(lambda raw: raw.as_export_dict() if isinstance(raw, WoKCitation) else raw, value))
                else:
                    export_dict[name] = value  # should be all basic fields now
            except (AttributeError, ValueError):
                export_dict[name] = None
                logger.warning(f"cannot export field [{name}] of {self}")
        return export_dict

    def has_attribute(self, attribute: str):
        try:
            _ = getattr(self, attribute)
            return True
        except ValueError:
            return False

    def validate_attributes(self):
        # validate key attributes and make sure they are valid
        for field in ['name', 'doi', 'journal']:
            if not self.has_attribute(field):
                raise ValueError(f'invalid article: no attribute "{field}"')
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise ValueError(f'invalid article: invalid attribute '
                                 f'"{field}" = {value}')
        if not self.has_attribute('year'):
            raise ValueError(f'invalid article: no attribute "year"')
        year_ = getattr(self, 'year')
        if not isinstance(year_, str) and (not isinstance(year_, int) or year_ not in range(1500, 2030)):
            raise ValueError(f'invalid article: invalid attribute: '
                             f'"year" = {year_}')
        if not self.has_attribute('citation'):
            raise ValueError(f'invalid article: no citation')
        citations = getattr(self, 'citation')
        if not isinstance(citations, list):
            raise ValueError(f'invalid article: '
                             f'invalid citation: "{citations}"')
        new_citation = []
        for citation in citations:
            if not isinstance(citation, WoKCitation):
                logger.warning(f'ignored invalid citation: '
                               f'"{citation}"')
                continue
            for field in ['first_author', 'doi', 'journal']:
                value = getattr(citation, field)
                if not isinstance(value, str) or not value:
                    logger.warning(f'ignored invalid citation: '
                                   f'invalid {field}: '
                                   f'"{value}"')
                    break
            else:
                year = citation.year
                if not isinstance(year, int) or \
                        year not in range(1500, 2030):
                    logger.warning(f'ignored invalid citation: '
                                   f'invalid year: "{year}"')
                    continue
                new_citation.append(citation)

        # update citation
        for attribute in self.attributes:
            if attribute.name == 'citation':
                attribute.value = new_citation

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
    def __init__(self, source: 'TextIO', start: int, end: int):
        self.source = source
        self.start, self.end = start, end
        self.root = etree.parse(self.source, etree.HTMLParser(recover=True, encoding='UTF-8'))

    def __repr__(self):
        return f"WokPrintList({self.start} -> {self.end})"

    def find_all_articles(self, year_range: Optional[range] = None):
        count = 0
        for table in self.root.xpath('//form[@id="printForm"]/table[not(@cellpadding)]'):
            count += 1
            try:
                article = WoKPrintArticle(table)
                article.validate_attributes()
                if not article.has_attribute('doi'):
                    logger.warning(f'article(name={article.title}) has no DOI, discarded')
                    continue
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
                logger.warning(f'cannot parse article {count}, skipped')
                logger.debug(f"exception says: {e}")

        if count == 0:
            logger.warning(f"{self} no articles found, this print list may be broken")
