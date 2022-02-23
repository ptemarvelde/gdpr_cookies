#!/usr/bin/env python
from selenium_driver_chrome import *
from dns_resolve import *
from rdap_query import *
from process_struct import *
from extract_processed_uris import *
from urllib.parse import urlparse
import time
import socket
from datetime import datetime
import psutil
import intervaltree
from netaddr import IPNetwork, IPAddress
import requests
import io
import multiprocessing
import sys


GL_browser_PAGE_LOAD_TIMEOUT = 60
GL_browser_RUN_HEADLESS = True
GL_CHROMEDRIVER_LOCK = multiprocessing.Lock()

# find the public IP from which we are fetching the information
GL_SOURCE_IP = str(json.loads(requests.get('http://jsonip.com').text)["ip"])

# stdout
GL_STDOUT_LOCK = multiprocessing.Lock()
# json output file
GL_OUTPUT_FILE = "./samples/example.json"
GL_OUTPUT_FID = io.open(GL_OUTPUT_FILE, 'a', encoding="utf-8")
GL_OUTPUT_LOCK = multiprocessing.Lock()
# exception file
GL_EXCEPTION_LOG_FILE = "./samples/example.log"
GL_EXCEPTION_LOG_FID = open(GL_EXCEPTION_LOG_FILE, 'a', encoding='utf-8')
GL_EXCEPTION_LOCK = multiprocessing.Lock()

# list of URIs already processed
GL_PROCESSED_URIS_DICT = get_list_processed_from_json(GL_OUTPUT_FILE)

# parallel browser instances
GL_MAX_NUM_CHROMEDRIVER_INSTANCES = 2
# chunks size to be processed in batch
GL_CRAWL_CHUNK_SIZE = 20
# sleep after processing a chunk
GL_CRAWL_CHUNK_SLEEP = 30

GL_URI_FILE = "./samples/uris.csv"
GL_MAX_DOMAINS_TO_CONTACT = 1000000
GL_SHUFFLE_DOMAINS_LIST = True

def load_domains_list(FNAME, LIMIT=1000000, SHUFFLE=True):
    rankdomains_list = []
    fid_input = open(FNAME, 'r')
    rank = 0
    for row in fid_input:
        row = row.replace("\n", "").strip()
        # if it looks like a valid domain
        if len(row) > 3 and len(row.split(".")) >= 2:
            # in case we have the format "rank,domain"
            if "," in row:
                rank, domain = row.split(",")
                rank = int(rank)
            else:
                rank = None
                domain = row
            if domain:
                rankdomains_list.append((rank, domain))
            LIMIT -= 1
            if LIMIT == 0:
                break
    fid_input.close()
    if SHUFFLE is True:
        random.shuffle(rankdomains_list)
    return rankdomains_list


def expand_with_protocols(RANKDOMAINS_LIST):
    rankuri_list = []
    for rank, domain in RANKDOMAINS_LIST:
        for proto in ["http://", "http://www.", "https://", "https://www."]:
            uri = "%s%s" % (proto, domain)
            # check that the uri is not in the list of those that were
            # already processed
            if uri not in GL_PROCESSED_URIS_DICT:
                rankuri_list.append((rank, uri))
    return rankuri_list


def check_if_ip(DOMAIN):
    try:
        domain = DOMAIN
        if domain.endswith("."):
            domain = domain[:-1]
        socket.inet_aton(domain)
        return True
    except socket.error:
        return False


def url_to_domain(URL):
    parsed_url = urlparse(URL)
    domain = parsed_url.netloc
    # if we have the port, we should remove it from the domain
    if parsed_url.port is not None:
        domain = domain.split(":")[0]
    if len(domain) == 0:
        domain = None
    return domain


def append_to_file(STRUCT):
    GL_OUTPUT_LOCK.acquire()
    GL_OUTPUT_FID.write(json.dumps(STRUCT)+"\n")
    GL_OUTPUT_FID.flush()
    GL_OUTPUT_LOCK.release()


def lock_print(STRING):
    GL_OUTPUT_LOCK.acquire()
    print(STRING)
    GL_OUTPUT_LOCK.release()


def log_exception(EXCEPTION_STR,
                  EXCEPTION_LOG_FILE,
                  EXCEPTION_LOG_FID=None):
    if EXCEPTION_LOG_FID is not None:
        EXCEPTION_LOG_FID.write(EXCEPTION_STR+"\n\n")
        EXCEPTION_LOG_FID.flush()
    else:
        fid = open(EXCEPTION_LOG_FILE, 'a')
        fid.write(EXCEPTION_STR+"\n")
        fid.close()


def lock_log_exception(EXC_STR):
    GL_EXCEPTION_LOCK.acquire()
    log_exception(EXCEPTION_STR=EXC_STR,
                  EXCEPTION_LOG_FILE=GL_EXCEPTION_LOG_FILE,
                  EXCEPTION_LOG_FID=GL_EXCEPTION_LOG_FID)
    GL_EXCEPTION_LOCK.release()


def kill_bg_processes():
    bg_proc_names = ["chrome",
                     "chromedriver",
                     "chrome-sandbox",
                     "google-chrome"]
    for proc in psutil.process_iter():
        try:
            if proc.name() in bg_proc_names:
                proc.kill()
        except psutil.NoSuchProcess:
            # if the process got removed in the meanwhile, we simply
            # ignore it
            pass


def fetch_info(ELEM):
    rank, uri = ELEM
    lock_print("%s => %s [rank: %s]" % (
        str(datetime.now()).split(".")[0], uri, rank))
    try:
        # selenium page loads...
        (page_source, page_title, resources_ordlist, redirection_chain,
         exception, exception_str, browserstart_ts,
         browserend_ts) = download_with_browser(
             URL=uri,
             RUN_HEADLESS=GL_browser_RUN_HEADLESS,
             PAGE_LOAD_TIMEOUT=GL_browser_PAGE_LOAD_TIMEOUT,
             CHROMEDRIVER_LOCK=GL_CHROMEDRIVER_LOCK)

        if (exception is None) and (len(resources_ordlist) >= 1):
            # generate a list of unique URLs
            unique_urls = set([el[0] for el in resources_ordlist])

            # generate a list of unique domains
            unique_mixed_domains = set([url_to_domain(url)
                                        for url in unique_urls])

            # filter out IPs and "None" entries from the list of
            # unique domains
            unique_domains = [d for d in unique_mixed_domains
                              if (d is not None)
                              and (check_if_ip(d) is False)]

            # resolve each domain with DNS
            unique_domains_resolutions = dict([
                (dom, recursively_resolve_domain(dom))
                for dom in unique_domains])

            ## NOTE: we could have inexistent domains which do not
            ## trigger any exception (i.e., the "answer" section
            ## is missing in the DNS response)

            # generate a list of unique IPs
            unique_ips = set([dnsresolutions[-1][1]
                              for dnsresolutions, dnsexception,
                              dnsexception_str,
                              dnsstart_ts, dnsend_ts
                              in unique_domains_resolutions.values()
                              # if the resolution was successful
                              if dnsexception is None and
                              dnsresolutions is not None])

            # collect the RDAP information for each IP
            rdap_infos_dict = {}
            for ip in unique_ips:
                if check_if_ip(ip):
                    rdap_infos_dict[ip] = download_info_using_rdap_cache(IP=ip)

            # dump the results into a json
            struct = generate_struct(
                SOURCE_IP=GL_SOURCE_IP,
                URI=uri,
                # browser
                PAGE_SOURCE=page_source,
                PAGE_TITLE=page_title,
                RESOURCES_ORDLIST=resources_ordlist,
                REDIRECTION_CHAIN=redirection_chain,
                EXCEPTION=exception,
                EXCEPTION_STR=exception_str,
                BROWSERSTART_TS=browserstart_ts,
                BROWSEREND_TS=browserend_ts,
                # dns
                UNIQUE_DOMAINS_RESOLUTIONS=unique_domains_resolutions,
                # rdap
                RDAP_INFOS_DICT=rdap_infos_dict)
        else:
            struct = generate_struct(SOURCE_IP=GL_SOURCE_IP,
                                     URI=uri,
                                     # browser
                                     PAGE_SOURCE=None,
                                     PAGE_TITLE=None,
                                     RESOURCES_ORDLIST=None,
                                     REDIRECTION_CHAIN=None,
                                     EXCEPTION=exception,
                                     EXCEPTION_STR=exception_str,
                                     BROWSERSTART_TS=browserstart_ts,
                                     BROWSEREND_TS=browserend_ts,
                                     # dns
                                     UNIQUE_DOMAINS_RESOLUTIONS=None,
                                     # rdap
                                     RDAP_INFOS_DICT=None)
        append_to_file(struct)
    except Exception as e:
        ts = str(datetime.now()).split(".")[0]
        exception = str(e).split("\n")[0]
        exception_str = "[%s] Exception: %s\n" % (ts, exception)
        exception_str += "* SCRIPT=integration.py\n"
        exception_str += "** FUNCTION=main\n"
        exception_str += "*** ELEM=%s\n" % (str(ELEM))
        exception_str += "**** %s" % traceback.format_exc()
        lock_log_exception(EXC_STR=exception_str)


def main():
    rankdomain_list = load_domains_list(FNAME=GL_URI_FILE,
                                        LIMIT=GL_MAX_DOMAINS_TO_CONTACT,
                                        SHUFFLE=GL_SHUFFLE_DOMAINS_LIST)
    # expand expand each string that represents a domain name with the
    # four prefixes: "http://", "http://www.", "https://",
    # "https://www." (in order to generate a valid URL that)
    rankuri_list = expand_with_protocols(rankdomain_list)

    tot_processed = 0
    # process in chunks
    for i in range(0, len(rankuri_list), GL_CRAWL_CHUNK_SIZE):
        p = multiprocessing.Pool(GL_MAX_NUM_CHROMEDRIVER_INSTANCES)
        chunk = rankuri_list[i: i+GL_CRAWL_CHUNK_SIZE]
        p.map(fetch_info, chunk)
        p.close()
        p.join()
        lock_print(("%s process completed crawling %s domains. "
                   "Sleeping %s seconds") % (
                       GL_MAX_NUM_CHROMEDRIVER_INSTANCES,
                       GL_CRAWL_CHUNK_SIZE,
                       GL_CRAWL_CHUNK_SLEEP))
        time.sleep(GL_CRAWL_CHUNK_SLEEP)
        kill_bg_processes()
        # just to be sure that everything was (hopefully!) shut down
        time.sleep(30)
        tot_processed += len(chunk)


if __name__ == "__main__":

    main()
