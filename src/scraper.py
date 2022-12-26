

# Author: Xiaoou Wang, Master’s student (currently in Paris) in NLP looking for a phd
# position/contrat cifre.
# [linkedin](https://www.linkedin.com/in/xiaoou-wang)/[email](mailto:xiaoouwangfrance@gmail.com)
# https://xiaoouwang.medium.com/complete-tutorial-on-scraping-french-news-from-le-monde-%EF%B8%8F-4fa92bc0a07b
# Have a look at https://soshace.com/responsible-web-scraping-gathering-data-ethically-and-legally/ before using the code.

import os  # helper functions like check file exists
import re
import sys
import datetime  # automatic file name
import numpy as np
import pandas as pd

from timer import Timer

import requests  # the following imports are common web scraping bundle
from urllib.request import urlopen  # standard python module
from bs4 import BeautifulSoup
from urllib.error import HTTPError
from collections import defaultdict
from collections import Counter

from urllib.error import URLError
from tqdm import tqdm
import pickle
import bz2
import _pickle as cPickle

from logger_utils import setup_this_run
from logger_utils import setup_logger
from logger_utils import log_machine


def extract_theme(link: str) -> str:
    """
    extracts theme from typical LeMonde html article link
    example:
        link = 'https://www.lemonde.fr/afrique/article/2021/01/01/rdc-au-moins-25-civils-tues-dans- ... .html'
        returns ' 'afrique' 
        
    :param link: (str) LeMonde article html link
    :return: (str) text after '.fr/' and before next '/'
    """

    try:
        theme_text = re.findall(r'.fr/.*?/', link)[0]
    except:
        pass
    else:
        return theme_text[4:-1]

@log_machine
def get_themes(ls_link) -> list:
    """
    parses list of links to identify theme in each, as defined in extract_theme()
    
    :param ls_link: 
    :return: list of themes
    """

    ls_theme = []

    for link in ls_link:
        theme = extract_theme(link)

        if theme is not None:
            ls_theme.append(theme)

    return ls_theme


@log_machine
def write_links(path, links, year_fn):
    with open(os.path.join(path + "/lemonde_" + str(year_fn) + "_links.txt"), 'w') as f:
        for link in links:
            f.write(link + "\n")


@log_machine
def write_to_file(filename, content):
    if os.path.exists(filename):
        with open(filename, 'a+') as f:
            f.write(str(content))
    else:
        with open(filename, 'w') as f:
            f.write(str(content))


@log_machine
def create_archive_links(year_start, year_end, month_start, month_end, day_start, day_end):
    archive_links = {}
    for y in range(year_start, year_end + 1):
        dates = [str(d).zfill(2) + "-" + str(m).zfill(2) + "-" +
                 str(y) for m in range(month_start, month_end + 1) for d in
                 range(day_start, day_end + 1)]
        archive_links[y] = [
            "https://www.lemonde.fr/archives-du-monde/" + date + "/" for date in dates]
    return archive_links


@log_machine
def get_articles_links(archive_links: list) -> list:
    """
    receives list of html links
    opens each page, interrogates some content to identify the links to save (not premium, not videos)
    :param archive_links: list of links to scrape
    :return: list of html links, screened for non-subscription and not-video
    """
    
    ls_links_non_abonne = []
    
    for link in archive_links:
        try:
            html = urlopen(link)
        except HTTPError as e:
            print("url not valid", link)
        else:
            soup = BeautifulSoup(html, "html.parser")
            news = soup.find_all(class_="teaser")
            
            for item in news:

                # condition here : if no span icon__premium (abonnes)
                if not item.find('span', {'class': 'icon__premium'}):
                    l_article = item.find('a')['href']
                    
                    # en-direct = video
                    if 'en-direct' not in l_article:
                        ls_links_non_abonne.append(l_article)
                        
    return ls_links_non_abonne


@log_machine
def classify_links(ls_theme: list, ls_link: list) -> dict:
    """

    :param ls_theme: list of themes, e.g., [internationale, sport, ..] to filter and add to dict
    :param ls_link: list of html links to review
    :return: dict, key = theme, value = html link
    """
    
    lx_link = defaultdict(list)
    
    for theme in ls_theme:
        theme_link = 'https://www.lemonde.fr/' + theme + '/article/'
        for link in ls_link:
            if theme_link in link:
                lx_link[theme].append(link)
                
    return lx_link


def get_single_page(url: str) -> tuple:
    """

    :param url: (str) html link
    :return: (tuple) (str(title), str(body))
    """
    try:
        html = urlopen(url)

    except HTTPError as e:
        print("url not valid", url)

    else:
        soup = BeautifulSoup(html, "html.parser")
        text_title = soup.find('h1')
        text_body = soup.article.find_all(["p", "h2"], recursive=False)
        return (text_title, text_body)


@log_machine
def scrape_articles(dict_links):

    themes = dict_links.keys()

    for theme in themes:

        create_folder(os.path.join('corpus', theme))

        logger.info("\processing:", theme)

        for i in tqdm(range(len(dict_links[theme]))):

            link = dict_links[theme][i]
            logger.info(str(link))

            fn = extract_fn(link)

            # ... get the article content
            single_page = get_single_page(link)

            if single_page is not None:

                with open((os.path.join('corpus', theme, fn + '.txt')), 'w') as f:
                    # f.write(dict_links[theme][i] + "\n" * 2)
                    f.write(single_page[0].get_text() + "\n" * 2)

                    for line in single_page[1]:
                        f.write(line.get_text() + "\n" * 2)

def extract_fn(lien):

    ls_one = lien.split('/')
    ls_two = ls_one[len(ls_one)-1].split('.')[0]

    return ls_two

@log_machine
def cr_corpus_dict(path_corpus, n_files=1000):

    dict_corpus = defaultdict(list)
    themes = os.listdir(path_corpus)
    print(path_corpus)
    print(themes)

    for theme in themes:
        counter = 0

        if not theme.startswith('.'):
            theme_directory = os.path.join(path_corpus, theme)

            for file in os.listdir(theme_directory):

                if counter < n_files:
                    path_file = os.path.join(theme_directory, file)
                    with open(path_file) as f:
                        text = f.read()

                    dict_corpus["label"].append(theme)
                    dict_corpus["text"].append(text)

                counter += 1

    return dict_corpus


@log_machine
def create_folder(path) -> None:
    
    if not os.path.exists(path):
        os.mkdir(path)
    else:
        print("folder exists already")
        
    return None

@log_machine
def create_archive_links(year_start: int, year_end: int,
                         month_start: int, month_end: int,
                         day_start: int, day_end: int) -> dict:

    lx_archive_link = {}

    for y in range(year_start, year_end + 1):
        
        dates = [str(d).zfill(2) + "-" + str(m).zfill(2) + "-" +
                 str(y) for m in range(month_start, month_end + 1) for d in
                 range(day_start, day_end + 1)]

        lx_archive_link[y] = [
            "https://www.lemonde.fr/archives-du-monde/" + date + "/" for date in dates]

    return lx_archive_link

# ...   -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# ...   main() routine
# ...   -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-


if __name__ == '__main__':

    config = setup_this_run(sys.argv)
    logger = setup_logger(sys.argv, config)
    logger.critical('start')

    # set timer for overall process timing
    tic = Timer()
    tic.start()

    # ... create dict of archival links
    if config['create_new_archive_links']:
        print('create archive links list')
        lx_archive_link = create_archive_links(
                                config['year_start'],
                                config['year_end'],
                                config['month_start'],
                                config['month_end'],
                                config['day_start'],
                                config['day_end'])

    corpus_path = os.path.join(os.getcwd(), config['corpus_links'])

    create_folder(corpus_path)
    lx_article_link = {}

    # ... write some links
    if config['get_new_article_links']:
        for year, ls_links in lx_archive_link.items():
            print("processing: ", year, ls_links)

            # ... get the article links !
            ls_article_link = get_articles_links(ls_links)
            lx_article_link[year] = ls_article_link

            # ... save links to text file
            write_links(corpus_path, ls_article_link, year)
    else:
        # ... read links from existing file(s)
        pass

    ls_theme = []

    # ... extract the theme text from html links text strings
    for ls_link in lx_article_link.values():
        ls_theme.extend(get_themes(ls_link))

    theme_stat = Counter(ls_theme)
    ls_top_theme = []

    # ...sort into themes
    for k, v in sorted(theme_stat.items(), key=lambda x: x[1], reverse=True):
        if v > config['n_theme']:
            ls_top_theme.append((k, v))
            
    print(ls_top_theme)

    all_links = []    # log final message
    # ... add all links to list
    for link_list in lx_article_link.values():
        all_links.extend(link_list)

    themes_top_five = [x[0] for x in ls_top_theme[:5]]
    themes_top_five_links = classify_links(themes_top_five, all_links)

    scrape_articles(themes_top_five_links)

    # ... create corpus
    path = 'corpus'
    dico_corpus = cr_corpus_dict(path, 1000)

    import json
    with open('lx_corpus.json', 'w') as convert_file:
        convert_file.write(json.dumps(dico_corpus))

    # log final message
    logger_msg = ' overall execution time = %.2f' % tic.stop()
    logger.critical('complete' + logger_msg)