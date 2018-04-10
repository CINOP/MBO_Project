import bs4 as bs
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import re
from splinter import Browser
import requests
import time
from requests import Request
from utils import ConfigDict

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
           "Host": "www.zoekscholen.onderwijsinspectie.nl"
           }

RESULTS_OUTPUT = 'config_file.txt'


class WebScrapper(object):
    """
    Class for Web Scrapping and Crawling. Although the class is generic as possible, it is narrowed
    to fit the needs of the project.
    """

    def __init__(self, source_url, write=True):
        """
        Args:
            source_url (str): The url of the page that we would like to crawl.
            write (boolean): If True the results of the
        """
        self.source_url = source_url
        self._browser = self.create_browser()
        self.write = write
        if self.write:
            self.openfile = ConfigDict(RESULTS_OUTPUT)

    def download(self, url, num_retries=2):
        """
        This method downloads a web page.  When a URL is passed, this function will download the web page
        and return the HTML.
        Often, the errors encountered when downloading are temporary. For example, the web server is overloaded
        and returns a 503 Service Unavailable error.
        For these errors, we can retry the download as the server problem may now be resolved.
        The download method only retires the 5xx errors.

        Parameters
        -------------------------
        url: String. The URL that we would like to download
        num_retries: Int, default 2. The number of retries

        Returns
        --------------------------
        The HTML of the URL
        """
        print('Downloading:', url)
        try:
            self.html = urlopen(url).read()
        except HTTPError as e:
            print(e)
        except URLError as e:
            print('Download error:', e.reason)
            self.html = None
            if num_retries > 2:
                print('I will give one more try')
                if hasattr(e, 'code') and 500 <= e.code < 600:
                    # Recursively retry 5xx HTTP errors
                    return self.download(url, num_retries - 1)
        return self.html

    def create_soup(self, link=None):
        """
        This method creates a BeatifulSoup (bsp) object which parses an HTML document and it is necessary
        for the other functions of the class.

        Parameters
        -------------------------
        link: str, default None. If None the URL pass in the constructor is used. Otherwise a URL that we would like
        to create a bsp object.

        Returns
        --------------------------
        A bsp object.
        """
        if link:
            link = link
        else:
            link = self.source_url
        downloadable = self.download(link)
        print('I am creating soup for', link)
        self.soup = bs.BeautifulSoup(downloadable, 'lxml')
        return self.soup

    def web_crawler(self, link, regex=None):
        """
        A method that crawls the content that we are interested to from a page. The function is modified in order
        to return all the links related with the regular expression passed as argument.

        Parameters
        -------------------------
        link: str. The web-page that we are interested to crawl.
        regex: str. A regular expression that can be used as a search key.

        Returns
        --------------------------
        A dict. Key is the name of the links and value is the URL.
        """
        with requests.Session() as s:
            req = Request('GET', link, headers=HEADERS)
            s.prepare_request(req)
            s.get(link, cookies={'from-my': 'browser'})
            req = s.get(link)
            soup_object = bs.BeautifulSoup(req.text, 'lxml')
            print(soup_object.find("div", {"id": "mainResults"}).find_all("h2")[0].text)
            # Start page
            start_page = soup_object.a
            start_page = start_page['href']
            links = {}
            if regex:
                for link, url in zip(soup_object.find_all('a', href=re.compile(regex)),
                                     soup_object.find_all('div', {'class': 'info'})):
                    page = start_page + link.get('href')
                    name = url.h3.text
                    links[name] = page
            else:
                for url in soup_object.find_all('a'):
                    links.append(start_page + url.get('href'))
            time.sleep(2)
        return links

    def web_access(self, link):
        """
        This method returns all the content of a web page that we are interested. Unfortunately, this method is modified
        in order to fit the needs of the project.
        Parameters
        -------------------------
        link: str. The web-page that we are interested to crawl.
        Returns
        --------------------------
        A dict. Key is the name of the program that we are interested to and as value the info that we would like
        to include.
        """
        soup_object = self.create_soup(link)
        # The name of the company
        company = soup_object.find('h1', {'class': 'heading'}).text
        print('The name of the company is:', company)
        browser = self._browser
        browser.visit(link)
        # Navigate the browser using x-path of the page element
        click_button_xpath = '//*[@id="tabs"]/ul/li[2]'  # based on the xpath
        click_button = browser.find_by_xpath(click_button_xpath)[0]
        click_button.click()
        # We will search for the info we need using the x-path and css syntax
        search_results_xpath = '//*[@class="remote-accordion ui-accordion ui-widget ui-helper-reset"]'
        search_results = browser.find_by_xpath(search_results_xpath)
        find_h = browser.find_by_css('div[class="l-1of4"]')
        scrapped_data = {}
        for search_result, label in zip(search_results, find_h):
            title = search_result.text
            label = label.text
            splited = title.split()
            scrapped_data[splited[0]] = {'institute': company, 'label': label, 'Details': splited[1:3]}
        if self.write:
            for key, value in scrapped_data.items():
                self.openfile[key] = value
        # Necessary in order to mimic a human behavior
        time.sleep(3)
        return scrapped_data

    def next_page(self, url):
        """
        This method crawls the next page.
        Parameters
        -------------------------
        url: str. The web start page
        Returns
        --------------------------
        str: The next page of the the start page

        Todo:
            *Extract the url of the next page using info from the start page.
        """
        with requests.Session() as s:
            req = Request('GET', url, headers=HEADERS)
            s.prepare_request(req)
            # s.get(url_2, cookies={'from-my': 'browser'})
            s.get(url, cookies={'from-my': 'browser'})
            req = s.get(url)
            soup = bs.BeautifulSoup(req.text, 'lxml')
            next_page = []
            next_page_number = None
            for page in soup.find_all('a', text=['Inspectie van het Onderwijs', 'Zoek en vergelijk']):
                next_page.append(page['href'])
            for page in soup.find_all('li', {'class': ['pager', 'next']}):
                next_page_number = int(page.a['href'][-1])
            try:
                assert (isinstance(int(next_page_number), int))
            except (AssertionError, TypeError, ValueError) as e:
                print('Problem in the next page function')
            print('Next page is:{}'.format(next_page_number))
            next_url = 'https://www.zoekscholen.onderwijsinspectie.nl/zoek-en-vergelijk?searchtype=generic&zoekterm=&pagina='  # noqa
            next_page = next_url + str(next_page_number) + '&filterSectoren=BVE'
            print(next_page)
        return next_page, next_page_number

    @staticmethod
    def create_browser():
        """
        Creates a browser window in Chrome
        """
        # Path for the chrome driver at the local machine
        executable_path = {'executable_path': r'C:\chromedriver_win32\chromedriver.exe'}
        # open a browser
        browser = Browser('chrome', **executable_path)
        return browser
