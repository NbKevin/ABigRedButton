"""
This original script was written by Yiyun Fan, yf855@nyu.edu.
It implemented a simple crawler interface scraping data from
Web of Knowledge (webofknowledge.com).

It has thereafter been modified and adapted by Kevin Ni,
kevin.ni@nyu.edu to work with A BIG RED BUTTON.
"""

import re
import math
# from threading import Thread
# from multiprocessing import Process
# from multiprocessing import Manager
import requests
import time
from time import sleep
import xlrd
from bs4 import BeautifulSoup
from lxml import etree
import csv
import argparse


class WoKSpider(object):
    # we assume this is correct for now
    # may be subject to change later if it does not work
    HEADERS = {
        'Origin': 'https://apps.webofknowledge.com',
        'Referer': 'https://apps.webofknowledge.com/WOS_AdvancedSearch_input.do?SID=8FSf73AbNMXZPYJSxKe&product=WOS&search_mode=AdvancedSearch',
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # template for the form 1
    FORM_1_TEMPLATE = {
        'fieldCount': 1,
        'action': 'search',
        'product': 'WOS',
        'search_mode': 'AdvancedSearch',
        'SID': sid,
        'max_field_count': 25,
        'formUpdated': 'true',
        'value(input1)': kanming,
        'value(select1)': 'LA',
        'value(input2)': 'English',
        'value(input3)': 'Article',
        'limitStatus': 'collapsed',
        'ss_lemmatization': 'On',
        'ss_spellchecking': 'Suggest',
        'SinceLastVisit_UTC': '',
        'SinceLastVisit_DATE': '',
        'period': 'Range Selection',
        'range': 'ALL',
        'startYear': '2015',
        'endYear': '2019',
        'update_back2search_link_param': 'yes',
        'advance_control': 'on',
        # 'ssStatus': 'display:none',
        # 'ss_showsuggestions': 'ON',
        'ss_query_language': 'auto',
        # 'ss_numDefaultGeneralSearchFields': 1,
        'rs_sort_by': 'PY.D;LD.D;SO.A;VL.D;PG.A;AU.A'
    }

    # similarly template for form 2
    FORM_2_TEMPLATE = {
        'product': 'WOS',
        'prev_search_mode': 'AdvancedSearch',
        'search_mode': 'CombineSearches',
        'SID': sid,
        'action': 'default',
        'goToPageLoc': 'SearchHistoryTableBanner',
        'currUrl': 'https://apps.webofknowledge.com/WOS_AdvancedSearch_input.do?product=WOS&search_mode=AdvancedSearch&SID=' + sid,
        # 'currUrl': 'https://apps.webofknowledge.com/WOS_CombineSearches_input.do?SID=' + sid + '&product=WOS&search_mode=CombineSearches',
        'x': 48,
        'y': 9,
        'dSet': 1
    }

    def make_form_1(self, sid: str, kanming: str):
        new_form = self.FORM_1_TEMPLATE.copy()
        new_form['SID'] = sid
        new_form['value(input1)'] = kanming
        return new_form

    def __init__(self, sid, kanming):
        self.form_data = {

        }
        self.form_data2 = {

        }

    def craw_nextpage(self, n_url, sid):
        # cursor = conn.cursor()
        parser = argparser.ArgumentParser()
        parser.add_argument('--start_record', type=int)
        parser.add_argument('--end_record', type=int)
        args = parser.parse_args()

        result_page = requests.get(n_url, headers={'User-Agent': 'Mozilla/5.0'})
        sid = re.findall(r'SID=\w+&', n_url)[0].replace('SID=', '').replace('&', '')
        self.craw_by_print(sid, args.start_record, args.end_record)

    def craw_by_print(self, sid, start, final):
        if final > (start + 49):
            end = start + 49
        else:
            end = final
        p_url = 'https://apps.webofknowledge.com/OutboundService.do?action=go&displayCitedRefs=true&displayTimesCited=true&displayUsageInfo=true&viewType=summary&product=WOS&mark_id=WOS&colName=WOS&search_mode=AdvancedSearch&locale=en_US&view_name=WOS-summary&sortBy=PY.D%3BLD.D%3BSO.A%3BVL.D%3BPG.A%3BAU.A&mode=outputService&qid=1&SID=' + sid + '&format=formatForPrint&filters=HIGHLY_CITED+HOT_PAPER+OPEN_ACCESS+PMID+USAGEIND+AUTHORSIDENTIFIERS+ACCESSION_NUM+FUNDING+SUBJECT_CATEGORY+JCR_CATEGORY+LANG+IDS+PAGEC+SABBR+CITREFC+ISSN+PUBINFO+KEYWORDS+CITTIMES+ADDRS+CONFERENCE_SPONSORS+DOCTYPE+CITREF+ABSTRACT+CONFERENCE_INFO+SOURCE+TITLE+AUTHORS++&selectedIds=&mark_to=' + str(
            end) + '&mark_from=' + str(
            start) + '&queryNatural=TS%3D((China+OR+PRC)+AND+(environment+OR+environmental+OR+green+OR+pollution+OR+sustainability+OR+sustainable))&count_new_items_marked=0&MaxDataSetLimit=&use_two_ets=false&DataSetsRemaining=&IsAtMaxLimit=&IncitesEntitled=no&value(record_select_type)=range&markFrom=' + str(
            start) + '&markTo=' + str(
            end) + '&fields_selection=HIGHLY_CITED+HOT_PAPER+OPEN_ACCESS+PMID+USAGEIND+AUTHORSIDENTIFIERS+ACCESSION_NUM+FUNDING+SUBJECT_CATEGORY+JCR_CATEGORY+LANG+IDS+PAGEC+SABBR+CITREFC+ISSN+PUBINFO+KEYWORDS+CITTIMES+ADDRS+CONFERENCE_SPONSORS+DOCTYPE+CITREF+ABSTRACT+CONFERENCE_INFO+SOURCE+TITLE+AUTHORS++&&'
        records = requests.get(p_url, headers={'User-Agent': 'Mozilla/5.0'})
        records.encoding = records.apparent_encoding
        tree = etree.HTML(records.text)
        num_records = end - start + 1
        for i in range(0, num_records):
            tables = tree.xpath('//form[@id="printForm"]/table[' + str(i + 2) + ']//text()')
            try:
                index = tables.index('Document Type:')
                if tables[index + 1] == '\nArticle':
                    index = tables.index('DOI:')
                    DOI_str = tables[index + 2]
                    print(DOI_str)

                    index = tables.index('Published:')
                    YoP = int(tables[index + 2][-4:])
                    print(YoP)

                    index = tables.index('Times Cited in Web of Science Core Collection:')
                    times_cited = int(tables[index + 2])
                    # print(times_cited)

                    index = tables.index('Title:')
                    title_str = tables[index + 2]
                    print(title_str)

                    index = tables.index('Source:')
                    journal_str = tables[index + 2]
                    print(journal_str)

                    index = tables.index('Abstract:')
                    abstract_str = tables[index + 1].strip('\n')
                    # print(abstract_str)

                    author_keywords = []
                    try:
                        index = tables.index('Author Keywords:')
                        a_key_str = tables[index + 1].strip('\n')
                        author_keywords = a_key_str.split('; ')
                    except:
                        pass
                    # print(author_keywords)

                    auto_keywords = []
                    try:
                        index = tables.index('KeyWords Plus:')
                        key_plus = tables[index + 1].strip('\n')
                        auto_keywords = key_plus.split('; ')
                    except:
                        pass
                    # print(auto_keywords)


                    author_info = []
                    index = tables.index('Addresses:')
                    addr_lst = tables[index + 1:]
                    index_end = addr_lst.index('\n')
                    addr_lst = addr_lst[:index_end]
                    for addr in addr_lst:
                        author = []
                        author = addr.split('] ')
                        author[0] = author[0].strip('\n[')
                        author[0] = author[0].split('; ')
                        author[1] = author[1].strip()  # univ address 1
                        author.append(author[1].split(', ')[0])  # univ 2
                        author.append(author[1].split(', ')[1])  # department 3
                        author_info.append(author)
                    # print(author_info)

                    index = tables.index('Cited References:')
                    cited_refs = tables[index + 1:]
                    index_end = cited_refs.index('\n')
                    cited_refs = cited_refs[:index_end]
                    cited_authors = []
                    for c_record in cited_refs:
                        c_record = c_record.strip('\n')
                        c_record = c_record.split(',')[0]
                        cited_authors.append(c_record)
                        # print(c_record)

                    file = open('article_data_general.csv', 'a', newline='')
                    writer = csv.writer(file)
                    writer.writerow([DOI_str, title_str, YoP, times_cited, journal_str, abstract_str])
                    file.close()

                    with open('article_keyword.csv', 'a', newline='') as file:
                        writer = csv.writer(file)
                        for keys in auto_keywords:
                            writer.writerow([DOI_str, keys])

                    with open('article_author_keywords.csv', 'a', newline='') as file:
                        writer = csv.writer(file)
                        for keys in author_keywords:
                            writer.writerow([DOI_str, keys])

                    with open('article_author.csv', 'a', newline='') as file:
                        writer = csv.writer(file)
                        for item in author_info:
                            for author in item[0]:
                                writer.writerow([DOI_str, author, item[2], item[1], item[3]])

                    with open('article_citation.csv', 'a', newline='') as file:
                        writer = csv.writer(file)
                        for item in cited_authors:
                            writer.writerow([DOI_str, item])

            except:
                pass
        if end != final:
            start = end + 1
            self.craw_by_print(sid, start, final)

    def craw_search(self, root_url):
        try:
            s = requests.Session()
            r = s.post(root_url, data=self.form_data, headers=self.hearders)
            r.encoding = r.apparent_encoding
            tree = etree.HTML(r.text)
            result_url = tree.xpath('//a[@id="hitCount"]/@href')
            p_num = tree.xpath('//a[@id="hitCount"]//text()')
            print(result_url)
            print(p_num)
            sid = re.findall(r'SID=\w+&', result_url[0])[0].replace('SID=', '').replace('&', '')

            self.craw_nextpage('https://apps.webofknowledge.com' + result_url[0], sid)

            return result_url
        except Exception as e:
            print(e)
            flag = 1
            return flag

    def delete_history(self):
        murl = 'https://apps.webofknowledge.com/WOS_CombineSearches.do'
        s = requests.Session()
        s.post(murl, data=self.form_data2, headers=self.hearders)


root_url = 'https://apps.webofknowledge.com/WOS_AdvancedSearch.do'

if __name__ == "__main__":
    root = 'http://www.webofknowledge.com/'
    s = requests.get(root)
    sid = re.findall(r'SID=\w+&', s.url)[0].replace('SID=', '').replace('&', '')

    search_key = 'TS=((China OR PRC) AND (environment OR environmental OR green OR pollution OR sustainability OR sustainable))'
    obj_spider = WoKSpider(sid, search_key)
    result_url = obj_spider.craw_search(root_url)
