#!/usr/bin/env python3
import logging
from pathlib import Path

import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import json
from collections import OrderedDict
import time as time
from datetime import datetime
import traceback
import re
from bs4 import BeautifulSoup
import os
from deep_translator import GoogleTranslator

USE_BRAVE = False

# NOTE: make sure that both binary and driver have the same version.
CHROME_SERVICE = Service(executable_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "chromedriver99.exe"))
BRAVE_BIN_PATH = "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

patterns = ['accept cookie', 'decline cookie', 'reject cookie', 'reject all cookie', 'cookie consent',
            'accept all cookies', 'cookie settings', 'I agree', 'I accept'
                                                                'OneTrust-Consent', 'Civic Cookie Control',
            'Clickio Consent Tool',
            'consentmanager.net', 'cookieBAR', 'Cookiebot', 'Cookie Consent', 'Cookie Information',
            'Crownpeak (Evidon)',
            'Didomi', 'jquery.cookieBar', 'jQuery EU Cookie Law popups', 'OneTrust', 'Quantcast Choice', 'TrustArc']
languages = ["de", "fr", "it", "no", "da", "fi", "es", "pt", "ro", "bg", "et", "el", "ga", "hr", "lv", "lt", "mt",
             "nl", "pl", "sv",
             "sk", "sl", "cs", "hu", "ru", "sr", "zh", "tr", "uk", "ar", "bs"]

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
    from pythia.task_manager import GL_SCREENSHOT_DIR

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
        chrome_options.add_argument("window-size=1980,960")

        # This excludes Devtools socket logging
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

        if USE_BRAVE:
            chrome_options.binary_location = BRAVE_BIN_PATH

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
                                  service=CHROME_SERVICE, )
        if (CHROMEDRIVER_LOCK is not None) and (lock_released is False):
            CHROMEDRIVER_LOCK.release()
            lock_released = True

        # Fetch the resource and all embedded URLs
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        req_timestamp = time.time()
        try:
            driver.get(URL)
        except Exception as e:
            driver.get(URL)

        cookies_list = driver.get_cookies()
        cookies = {
            "request_timestamp": req_timestamp,
            "cookies": cookies_list
        }
        # sleep to let banner appear
        time.sleep(5)

        screenshot_path: str = str((GL_SCREENSHOT_DIR / (URL.replace('://', '_') + ".png")).resolve())
        if not driver.save_screenshot(str(screenshot_path)):
            screenshot_path = "Screenshot failed"

        # We need to put it into a variable, otherwise when
        # calling again "driver.get_log('performance')" it will
        # return None.
        driver_network_log_messages = get_new_netlog_msgs(DRIVER=driver)

        landing_url_reachable = True
        for message in driver_network_log_messages:
            if (message["method"] == "Page.frameNavigated") and \
                    ("params" in message) and \
                    ("frame" in message["params"]) and \
                    ("unreachableUrl" in message["params"]["frame"] and
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
                        tot_slept.append(tot_slept[-1] + tot_slept[-2])
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
        # raise e
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

    # detecting banner
    banner_detected = (detect_banner_keywords() or detect_banner_cookie_libs())

    return (page_source, page_title, resources_ordlist,
            redirection_chain, exception, exception_str,
            start_ts, end_ts, cookies, banner_detected,
            screenshot_path)


# Translate the given word to the given language. The language should be in abbreviation form, e.g 'nl' or 'de'.
def translate(word, lang):
    return GoogleTranslator(source='auto', target=lang).translate(word)


def detect_banner_keywords() -> bool:
    for lang in languages:
        external_patterns = map(lambda x: translate(x, lang), patterns)
        patterns.extend(external_patterns)
    # dutch_patterns = map(lambda x: translate(x, 'nl'), patterns)
    # patterns.extend(dutch_patterns)

    if page_source:
        for pattern in patterns:
            if re.search(pattern, page_source, flags=re.IGNORECASE):
                return True
    return False


def detect_banner_cookie_libs() -> bool:
    lib_js_file_names = [
        "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.x\.min\.js",  # Civic Cookie Control
        "https://cc\.cdn\.civiccomputing\.com/9/cookieControl-9\.5\.min\.js",
        "clickio\.mgr\.consensu\.org/t/consent_225761\.js",  # Clickio Consent Tool
        'window.gdprAppliesGlobally=true;if(!("cmp_id" in window)||window.cmp_id<1){window.cmp_id=0}if(!("cmp_cdid" in window))'
        '{window.cmp_cdid="3834f5ec2941"}if(!("cmp_params" in window)){window.cmp_params=""}if(!("cmp_host" in window))'
        '{window.cmp_host="d.delivery.consentmanager.net"}if(!("cmp_cdn" in window)){window.cmp_cdn="cdn.consentmanager.net"}'
        'if(!("cmp_proto" in window)){window.cmp_proto="https:"}if(!("cmp_codesrc" in window)){window.cmp_codesrc="1"}'
        'window.cmp_getsupportedLangs=function(){var b=["DE","EN","FR","IT","NO","DA","FI","ES","PT","RO","BG","ET","EL","GA","HR","LV","LT","MT","NL","PL","SV","SK","SL","CS","HU","RU","SR","ZH","TR","UK","AR","BS"];'
        'if("cmp_customlanguages" in window){for(var a=0;a<window.cmp_customlanguages.length;a++)'
        '{b.push(window.cmp_customlanguages[a].l.toUpperCase())}}return b};window.cmp_getRTLLangs=function()'
        '{return["AR"]};window.cmp_getlang=function(j){if(typeof(j)!="boolean"){j=true}'
        'if(j&&typeof(cmp_getlang.usedlang)=="string"&&cmp_getlang.usedlang!=="")'
        '{return cmp_getlang.usedlang}var g=window.cmp_getsupportedLangs();var c=[];'
        'var f=location.hash;var e=location.search;var a="languages" in navigator?navigator.languages:[];if(f.indexOf("cmplang=")!=-1){c.push(f.substr(f.indexOf("cmplang=")+8,2).toUpperCase())}else{if(e.indexOf("cmplang=")!=-1)'
        '{c.push(e.substr(e.indexOf("cmplang=")+8,2).toUpperCase())}else{if("cmp_setlang" in window&&window.cmp_setlang!=""){c.push(window.cmp_setlang.toUpperCase())}else{if(a.length>0){for(var d=0;d<a.length;d++){c.push(a[d])}}}}}'
        'if("language" in navigator){c.push(navigator.language)}if("userLanguage" in navigator){c.push(navigator.userLanguage)}var h="";for(var d=0;d<c.length;d++){var b=c[d].toUpperCase();if(g.indexOf(b)!=-1){h=b;break}if(b.indexOf("-")!=-1){b=b.substr(0,2)}if(g.indexOf(b)!=-1){h=b;break}}'
        'if(h==""&&typeof(cmp_getlang.defaultlang)=="string"&&cmp_getlang.defaultlang!==""){return cmp_getlang.defaultlang}else{if(h==""){h="EN"}}h=h.toUpperCase();return h};(function(){var n=document;var p=window;var f="";var b="_en";if("cmp_getlang" in p){f=p.cmp_getlang().toLowerCase();'
        'if("cmp_customlanguages" in p){for(var h=0;h<p.cmp_customlanguages.length;h++){if(p.cmp_customlanguages[h].l.toUpperCase()==f.toUpperCase()){f="en";break}}}b="_"+f}function g(e,d){var l="";e+="=";var i=e.length;if(location.hash.indexOf(e)!=-1)'
        '{l=location.hash.substr(location.hash.indexOf(e)+i,9999)}else{if(location.search.indexOf(e)!=-1){l=location.search.substr(location.search.indexOf(e)+i,9999)}else{return d}}if(l.indexOf("&")!=-1){l=l.substr(0,l.indexOf("&"))}return l}var '
        'j=("cmp_proto" in p)?p.cmp_proto:"https:";var o=["cmp_id","cmp_params","cmp_host","cmp_cdn","cmp_proto"];for(var h=0;h<o.length;h++){if(g(o[h],"%%%")!="%%%"){window[o[h]]=g(o[h],"")}}var k=("cmp_ref" in p)?p.cmp_ref:location.href;'
        'var q=n.createElement("script");q.setAttribute("data-cmp-ab","1");var c=g("cmpdesign","");var a=g("cmpregulationkey","");q.src=j+"//"+p.cmp_host+"/delivery/cmp.php?"+("cmp_id" in p&&p.cmp_id>0?"id="+p.cmp_id:"")+("cmp_cdid" in p?"cdid="+p.cmp_cdid:"")+"&h="+encodeURIComponent(k)+(c!=""?"&cmpdesign="+encodeURIComponent(c):"")+(a!=""?"&cmpregulationkey="+'
        'encodeURIComponent(a):"")+("cmp_params" in p?"&"+p.cmp_params:"")+(n.cookie.length>0?"&__cmpfcc=1":"")+"&l="+f.toLowerCase()+"&o="+(new Date()).getTime();q.type="text/javascript";q.async=true;if(n.currentScript){n.currentScript.parentElement.appendChild(q)}else{if(n.body){n.body.appendChild(q)}else{var m=n.getElementsByTagName("body");if(m.length==0)'
        '{m=n.getElementsByTagName("div")}if(m.length==0){m=n.getElementsByTagName("span")}if(m.length==0){m=n.getElementsByTagName("ins")}if(m.length==0){m=n.getElementsByTagName("script")}if(m.length==0){m=n.getElementsByTagName("head")}if(m.length>0){m[0].appendChild(q)}}}var q=n.createElement("script");q.src=j+"//"+p.cmp_cdn+"/delivery/js/cmp"+b+".min.js";'
        'q.type="text/javascript";q.setAttribute("data-cmp-ab","1");q.async=true;if(n.currentScript){n.currentScript.parentElement.appendChild(q)}else{if(n.body){n.body.appendChild(q)}else{var m=n.getElementsByTagName("body");if(m.length==0){m=n.getElementsByTagName("div")}if(m.length==0){m=n.getElementsByTagName("span")}if(m.length==0)'
        '{m=n.getElementsByTagName("ins")}if(m.length==0){m=n.getElementsByTagName("script")}if(m.length==0){m=n.getElementsByTagName("head")}if(m.length>0){m[0].appendChild(q)}}}})();window.cmp_addFrame=function(b){if(!window.frames[b]){if(document.body){var a=document.createElement("iframe");a.style.cssText="display:none";a.name=b;document.body.appendChild(a)}'
        'else{window.setTimeout(window.cmp_addFrame,10,b)}}};window.cmp_rc=function(h){var b=document.cookie;var f="";var d=0;while(b!=""&&d<100){d++;while(b.substr(0,1)==" "){b=b.substr(1,b.length)}var g=b.substring(0,b.indexOf("="));if(b.indexOf(";")!=-1){var c=b.substring(b.indexOf("=")+1,b.indexOf(";"))}else{var c=b.substr(b.indexOf("=")+1,b.length)}if(h==g){f=c}'
        'var e=b.indexOf(";")+1;if(e==0){e=b.length}b=b.substring(e,b.length)}return(f)};window.cmp_stub=function(){var a=arguments;__cmapi.a=__cmapi.a||[];if(!a.length){return __cmapi.a}else{if(a[0]==="ping"){if(a[1]===2){a[2]({gdprApplies:gdprAppliesGlobally,cmpLoaded:false,cmpStatus:"stub",displayStatus:"hidden",apiVersion:"2.0",cmpId:31},true)}else{a[2](false,true)}}'
        'else{if(a[0]==="getUSPData"){a[2]({version:1,uspString:window.cmp_rc("")},true)}else{if(a[0]==="getTCData"){__cmapi.a.push([].slice.apply(a))}else{if(a[0]==="addEventListener"||a[0]==="removeEventListener"){__cmapi.a.push([].slice.apply(a))}else{if(a.length==4&&a[3]===false){a[2]({},false)}else{__cmapi.a.push([].slice.apply(a))}}}}}}};window.cmp_msghandler=function(d)'
        '{var a=typeof d.data==="string";try{var c=a?JSON.parse(d.data):d.data}catch(f){var c=null}if(typeof(c)==="object"&&c!==null&&"__cmpCall" in c){var b=c.__cmpCall;window.__cmp(b.command,b.parameter,function(h,g){var e={__cmpReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__cmapiCall" in c)'
        '{var b=c.__cmapiCall;window.__cmapi(b.command,b.parameter,function(h,g){var e={__cmapiReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__uspapiCall" in c){var b=c.__uspapiCall;window.__uspapi(b.command,b.version,function(h,g){var e={__uspapiReturn:{returnValue:h,success:g,callId:b.callId}}'
        ';d.source.postMessage(a?JSON.stringify(e):e,"*")})}if(typeof(c)==="object"&&c!==null&&"__tcfapiCall" in c){var b=c.__tcfapiCall;window.__tcfapi(b.command,b.version,function(h,g){var e={__tcfapiReturn:{returnValue:h,success:g,callId:b.callId}};d.source.postMessage(a?JSON.stringify(e):e,"*")},b.parameter)}};window.cmp_setStub=function(a){if(!(a in window)||'
        '(typeof(window[a])!=="function"&&typeof(window[a])!=="object"&&(typeof(window[a])==="undefined"||window[a]!==null))){window[a]=window.cmp_stub;window[a].msgHandler=window.cmp_msghandler;window.addEventListener("message",window.cmp_msghandler,false)}};window.cmp_addFrame("__cmapiLocator");window.cmp_addFrame("__cmpLocator");window.cmp_addFrame("__uspapiLocator");'
        'window.cmp_addFrame("__tcfapiLocator");window.cmp_setStub("__cmapi");window.cmp_setStub("__cmp");window.cmp_setStub("__tcfapi");window.cmp_setStub("__uspapi");',
        # consentmanager.net
        'd\.delivery\.consentmanager\.net',  # consentmanager.net
        'https://cdn\.consentmanager\.net/delivery/autoblocking/3834f5ec2941\.js',  # consentmanager.net
        'https://cdn\.jsdelivr\.net/npm/cookie-bar/cookiebar-latest.min\.js',  # cookieBAR
        '<a href=\"#\" onclick=\"document\.cookie=\'cookiebar=;expires=Thu, 01 Jan 1970 00:00:01 GMT;path=/\'; setupCookieBar\(\); return false;\">Click here to revoke the Cookie consent</a>',
        # cookieBAR
        '(https:\/\/|http:\/\/)?consent\.cookiebot\.com\/.*\.js',  # Cookiebot
        '((cdn\.jsdelivr\.net).*|window\.)cookieconsent(\.js|\.css|\.min\.js|\.min\.css|\.initialise)',
        # Cookie Consent
        # 'https://cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.css', # Cookie Consent
        # 'https://cdn.jsdelivr.net/npm/cookieconsent@3/build/cookieconsent.min.js', # Cookie Consent
        # 'window.cookieconsent.initialise', # Cookie Consent
        'https://policy\.app\.cookieinformation\.com/uc\.js',  # Cookie Information
        '(https:|http:)?//cdn.cookie-script.com/.*.js',  # Cookie Script
        'evidon-banner\.js',  # Crownpeak (Evidon)
        'evidon.*.js',  # Crownpeak (Evidon)
        'didomi',  # Didomi
        '(jquery\.|\.)?cookieBar(\.js|\.css)?',  # jquery.cookieBar
        'jquery-eu-cookie-law-popup(\.js|\.css)',  # jQuery EU Cookie Law popups
        'user_cookie_already_accepted|user_cookie_consent_changed',  # jQuery EU Cookie Law popups (events regex)
        'otBannerSdk(\.js)?|(ot|onetrust)-banner(-sdk)?|(window\.)?OneTrust(\.LoadBanner)?',  # OneTrust
        'Quantcast|window\._qevents|pixel\.quantserve\.com(\/pixel)?',  # Quantcast Choice
        'truste-consent-button|truste-consent-required|truste-show-consent|consent\.trustarc\.com',  # TrustArc (TRUSTe)
        '',  # Cookie Bar (WordPress Plugins)
        '',  # Cookie Consent
        '',  # Cookie Law Bar
        '',  # Cookie Notice for GDPR
        '',  # Custom Cookie Message
        '',  # EU Cookie Law
        '',  # GDPR Cookie Compliance
        '',  # GDPR Cookie Consent
        '',  # GDPR Tools
        '',  # WF Cookie Consent
        '',  # Cookie Control (Drupal Modules)
        '',  # EU Cookie Compliance
        '',  # Simple Cookie Compliance
    ]
    if page_source:
        for pattern in lib_js_file_names:
            if re.search(pattern, page_source, flags=re.IGNORECASE):
                return True
    return False


if __name__ == "__main__":

    # Example: HTTPS with Chromium in headless mode
    url = "https://bitbucket.org/"
    (page_source, page_title, resources_ordlist, redirection_chain,
     exception, exception_str, browserstart_ts,
     browserend_ts, cookies) = download_with_browser(url)
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
    print("cookies:", json.dumps(cookies, indent=4))
    print("Time spent: %4.2f seconds" % (browserend_ts - browserstart_ts))
    print()
