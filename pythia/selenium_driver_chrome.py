#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
from collections import OrderedDict
import time as time
from datetime import datetime
import traceback
from bs4 import BeautifulSoup

if ('gl_PATH_CHROMEDRIVER' not in globals()) or \
   ('gl_PATH_CHROME_BROWSER' not in globals()) or \
   ('gl_SPOOFED_USER_AGENT' not in globals()):
    gl_PATH_CHROMEDRIVER = "/usr/local/bin/chromedriver"
    gl_PATH_CHROME_BROWSER = "/usr/bin/google-chrome"
    gl_SPOOFED_USER_AGENT = ("Mozilla/5.0 (X11; Linux x86_64) "
                             "AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/70.0.3538.77 "
                             "Safari/537.36")


def download_with_browser(URL,
                          RUN_HEADLESS=True,
                          MIN_PAGE_LOAD_TIMEOUT=4,
                          PAGE_LOAD_TIMEOUT=60,
                          CHROMEDRIVER_LOCK=None):

    def get_new_netlog_msgs(DRIVER):
        try:
            return [json.loads(elem["message"])["message"]
                    for elem in DRIVER.get_log('performance')
                    if "message" in elem]
        except Exception as e:
            return []

    def got_response_for_all_requests(NETLOG_PERFORMANCE):
        received_responses_dict = {}
        for message in NETLOG_PERFORMANCE:
            if message["method"] == "Network.requestWillBeSent":
                url = message["params"]["request"]["url"]
                if not url.startswith("data:"):
                    received_responses_dict[url] = False
        for message in NETLOG_PERFORMANCE:
            if message["method"] == "Network.responseReceived":
                url = message["params"]["response"]["url"]
                if not url.startswith("data:"):
                    received_responses_dict[url] = True
            elif message["method"] == "Network.requestWillBeSent":
                if "redirectResponse" in message["params"]:
                    url = message["params"]["redirectResponse"]["url"]
                    received_responses_dict[url] = True
        return len([v for v in received_responses_dict.values()
                    if v is False]) == 0

    # The code snippet outputs a dictionary of pairs "(url,
    # content-type)", where "url" is the url pointing to each resource
    # downloaded by the browser and "content-type" is the type of the
    # resource according to the headers sent by the web server.

    page_source = None
    page_title = None
    current_url, current_source, current_title = None, None, None
    resources_ordlist = []
    redirection_chain = None
    tmp_redirection_chain, loaded_urls = [], []
    exception = None
    exception_str = None
    lock_released = False
    start_ts, end_ts = time.time(), time.time()
    try:
        # Options used when launching Chrome
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('disable-extensions')
        chrome_options.add_argument("ignore-certificate-errors")
        chrome_options.add_argument("incognito")
        chrome_options.add_argument("disable-gpu")
        chrome_options.add_argument("disable-xss-auditor")
        chrome_options.add_argument("disable-background-networking")
        chrome_options.add_argument("mute-audio")
        # notifications
        chrome_options.add_argument("disable-notifications")
        chrome_options.add_argument("disable-file-system")
        chrome_options.add_argument("allow-running-insecure-content")
        if RUN_HEADLESS is True:
            chrome_options.add_argument("headless")
        if gl_SPOOFED_USER_AGENT:
            chrome_options.add_argument("--user-agent=%s" %
                                        gl_SPOOFED_USER_AGENT)

        caps = DesiredCapabilities.CHROME
        caps["binary_location"] = gl_PATH_CHROME_BROWSER
        # Needed for non-trusted HTTPS certificates (with 'headless'
        # mode chromedriver will ignore the other options!)
        ## ISSUE https://bugs.chromium.org/p/chromedriver/issues/detail?id=1925
        caps['acceptInsecureCerts'] = True

        # Options for instructing the browser to log the network
        # traffic visible to the user
        caps['goog:loggingPrefs'] = {
            "browser": "ALL",
            "driver": "ALL",
            "performance": "ALL"}

        if CHROMEDRIVER_LOCK is not None:
            CHROMEDRIVER_LOCK.acquire()
        driver = webdriver.Chrome(desired_capabilities=caps,
                                  options=chrome_options,
                                  executable_path=gl_PATH_CHROMEDRIVER)
        if (CHROMEDRIVER_LOCK is not None) and (lock_released is False):
            CHROMEDRIVER_LOCK.release()
            lock_released = True

        # Fetch the resource and all embedded URLs
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.get(URL)

        # We need to put it into a variable, otherwise when
        # calling again "driver.get_log('performance')" it will
        # return None.
        driver_network_log_messages = get_new_netlog_msgs(DRIVER=driver)

        landing_url_reachable = True
        for message in driver_network_log_messages:
            if (message["method"] == "Page.frameNavigated") and \
               ("params" in message) and \
               ("frame" in message["params"]) and \
               ("unreachableUrl" in message["params"]["frame"] and \
        message["params"]["frame"]["unreachableUrl"] == driver.current_url):
                landing_url_reachable = False
        if landing_url_reachable:
            # if there's a minimum waiting treshold, we wait in case
            # there are some redirects fired after a timeout...
            if MIN_PAGE_LOAD_TIMEOUT > 0:
                time.sleep(MIN_PAGE_LOAD_TIMEOUT)
                driver_network_log_messages += get_new_netlog_msgs(
                        DRIVER=driver)
                PAGE_LOAD_TIMEOUT -= MIN_PAGE_LOAD_TIMEOUT
            tot_slept, s = [0], 0
            while s < PAGE_LOAD_TIMEOUT:
                if got_response_for_all_requests(
                        driver_network_log_messages) is True:
                    break
                else:
                    time.sleep(tot_slept[-1])
                    driver_network_log_messages += get_new_netlog_msgs(
                        DRIVER=driver)
                    # Fibonacci :-)
                    if len(tot_slept) == 1:
                        tot_slept.append(1)
                    else:
                        tot_slept.append(tot_slept[-1]+tot_slept[-2])
                        s = sum(tot_slept)
                        if s > PAGE_LOAD_TIMEOUT:
                            tot_slept[-1] -= s - PAGE_LOAD_TIMEOUT

        # Then we process the responses and we update the
        # "Content-Type" for each URL for which we sent an HTTP
        # Request (and received the corresponding HTTP Response).
        for message in driver_network_log_messages:
            method = message["method"]
            if method == "Network.responseReceived":
                url = message["params"]["response"]["url"]
                data = message["params"]["response"]
                resources_ordlist.append((url, data))
            elif (method == "Network.requestWillBeSent") and \
                 ("redirectResponse" in message["params"]):
                url = message["params"]["redirectResponse"]["url"]
                data = message["params"]["redirectResponse"]
                resources_ordlist.append((url, data))
                url_from = url
                url_to = message["params"]["request"]["url"]
                tmp_redirection_chain.append((url_from, url_to))
            elif method == "Page.frameNavigated":
                if ("params" in message) and \
                   ("frame" in message["params"]) and \
                   ("parentId" not in message["params"]["frame"]):
                    if "unreachableUrl" in message["params"]["frame"]:
                        url = message["params"]["frame"]["unreachableUrl"]
                    elif "url" in message["params"]["frame"]:
                        url = message["params"]["frame"]["url"]
                    if not url.startswith("data:"):
                        loaded_urls.append(url)
            elif method == "Page.navigatedWithinDocument":
                if ("params" in message) and \
                   ("url" in message["params"]):
                    url = message["params"]["url"]
                    if not url.startswith("data:"):
                        loaded_urls.append(url)
            elif method == "Page.frameScheduledNavigation":
                if ("url" in message["params"]) and \
                   ("reason" in message["params"]) and \
                   (message["params"]["reason"] == "metaTagRefresh"):
                    url = message["params"]["url"]
                    loaded_urls.append(url)
        current_url = driver.current_url
        current_source = driver.page_source
        current_title = driver.title
        # In case the the browser, instead of using the content of the
        # "<title>" tag as title of the page, select a WebElement
        # (e.g., an image) as title
        if isinstance(current_title,
                      webdriver.remote.webelement.WebElement):
            soup = BeautifulSoup(current_source, 'lxml')
            current_title = soup.title.text
        # close all tabs one-by-one
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            driver.close()
    except Exception as e:
        ts = str(datetime.now()).split(".")[0]
        exception = str(e).split("\n")[0]
        exception_str = "[%s] Exception: %s\n" % (ts, exception)
        exception_str += "* SCRIPT=selenium_driver_chrome.py\n"
        exception_str += "** FUNCTION=download_with_browser\n"
        exception_str += "*** URL=%s\n" % (URL)
        exception_str += "*** RUN_HEADLESS=%s\n" % (RUN_HEADLESS)
        exception_str += "*** PAGE_LOAD_TIMEOUT=%s\n" % (PAGE_LOAD_TIMEOUT)
        exception_str += "**** %s" % traceback.format_exc()
    finally:
        if len(loaded_urls) > 0:
            # the first URL might not have been loaded, so we add it manually
            if loaded_urls[0] != URL:
                loaded_urls.insert(0, URL)
        # we build the redirection chain backwards from the last
        # URL that was loaded in the browser
        redirection_chain = []
        while len(loaded_urls) > 0:
            url = loaded_urls.pop(-1)
            if len(redirection_chain) == 0 or redirection_chain[0] != url:
                redirection_chain.insert(0, url)
                pos = [i for i, elem in enumerate(tmp_redirection_chain)
                       if elem[1] == url]
                # if we had an HTTP redirect among pages
                if len(pos) > 0:
                    pos = pos[-1]
                    for i in range(pos, 0, -1):
                        url_from, url_to = tmp_redirection_chain[i]
                        if url_to == redirection_chain[0]:
                            redirection_chain.insert(0, url_from)
        if (len(redirection_chain) >= 1) and \
           (redirection_chain[-1] == current_url) and \
           landing_url_reachable is True:
            # Get the HTML source and the <title>
            page_source = current_source
            page_title = current_title
        else:
            ts = str(datetime.now()).split(".")[0]
            exception = "unreachableUrl"
            exception_str = "[%s] Exception: %s\n" % (ts, exception)
            exception_str += "* SCRIPT=selenium_driver_chrome.py\n"
            exception_str += "** FUNCTION=download_with_browser\n"
            exception_str += "*** URL=%s\n" % (URL)
            exception_str += "*** RUN_HEADLESS=%s\n" % (RUN_HEADLESS)
            exception_str += "*** PAGE_LOAD_TIMEOUT=%s\n" % (PAGE_LOAD_TIMEOUT)
        if 'driver' in locals():
            driver.quit()
        # one last check to make sure that we did release the lock
        # also in case an exception occurred!
        if (CHROMEDRIVER_LOCK is not None) and (lock_released is False):
            CHROMEDRIVER_LOCK.release()
    end_ts = time.time()
    return (page_source, page_title, resources_ordlist,
            redirection_chain, exception, exception_str,
            start_ts, end_ts)


if __name__ == "__main__":

    # Example: HTTPS with Chromium in headless mode
    url = "https://bitbucket.org/srdjanmatic/pythia.git"
    (page_source, page_title, resources_ordlist, redirection_chain,
     exception, exception_str, browserstart_ts,
     browserend_ts) = download_with_browser(url)
    print("Start URL: %s" % (url))
    if exception is None:
        print("redirection_chain: %s" % (" => ".join([
            el for el in redirection_chain])))
        print()
        print(resources_ordlist[0])
        for (url, data) in resources_ordlist:
            print("URL: %s\n" % (url))
            if "requestHeaders" in data:
                print("REQUEST HEADERS:")
                for k, v in data["requestHeaders"].items():
                    if not k.startswith(":"):
                        print("-> %s: %s" % (k, v))
            if "headers" in data:
                print("RESPONSE HEADERS:")
                for k, v in data["headers"].items():
                    print("<- %s: %s" % (k, v))
            print()
    else:
        print("Exception: %s" % (exception))
        print()
    print("Time spent: %4.2f seconds" % (browserend_ts - browserstart_ts))
    print()
