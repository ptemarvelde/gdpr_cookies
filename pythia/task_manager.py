#!/usr/bin/env python
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import psutil
import requests
from tqdm import tqdm

from banner_config import get_banner_patterns
from dns_resolve import *
from extract_processed_uris import *
from process_struct import *
from rdap_query import *
from selenium_driver_chrome import download_with_browser

sys.path.append("../")
from util.utils import load_output

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../util"))

GL_browser_PAGE_LOAD_TIMEOUT = 60
GL_browser_RUN_HEADLESS = True
GL_CHROMEDRIVER_LOCK = multiprocessing.Lock()
INCLUDE_RDAP = True

# find the public IP from which we are fetching the information
GL_SOURCE_IP = str(json.loads(requests.get('http://jsonip.com').text)["ip"])

# stdout
GL_STDOUT_LOCK = multiprocessing.Lock()

# json output file
GL_OUTPUT_LOCK = multiprocessing.Lock()

# exception file
GL_EXCEPTION_LOCK = multiprocessing.Lock()

# parallel browser instances
GL_MAX_NUM_CHROMEDRIVER_INSTANCES = 1
# chunks size to be processed in batch
GL_CRAWL_CHUNK_SIZE = 20
# sleep after processing a chunk
GL_CRAWL_CHUNK_SLEEP = 30

# GL_URI_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), Path("../resources/input/dutch_top_50.csv"))
GL_URI_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), Path("../resources/testdomains.txt"))

# GL_URI_FILE = "../util/data/dutch_top_50"
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
    lock_print(f"querying domains: {rankdomains_list}")
    return rankdomains_list


def expand_with_protocols(RANKDOMAINS_LIST, GL_PROCESSED_URIS_DICT):
    rankuri_list = []
    protocols = ["https://www."]
    for rank, domain in RANKDOMAINS_LIST:
        # Only use https://www, difference in cookies/banners for different protocols is minimal.
        # for proto in ["http://", "http://www.", "https://", "https://www."]:
        for proto in ["https://www."]:
            uri = "%s%s" % (proto, domain)
            # check that the uri is not in the list of those that were
            # already processed
            if uri in GL_PROCESSED_URIS_DICT:
                lock_print(f"Skipping {uri} as it was already processed before")
            else:
                rankuri_list.append((rank, uri))
    lock_print(f"Querying {len(rankuri_list)} uri's of {RANKDOMAINS_LIST} given domains, {protocols = }")
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


def append_to_file(STRUCT, GL_OUTPUT_PATH):
    GL_OUTPUT_LOCK.acquire()
    fid = open(GL_OUTPUT_PATH, 'a+')
    fid.write(json.dumps(STRUCT) + "\n")
    fid.close()
    GL_OUTPUT_LOCK.release()


def lock_print(STRING):
    GL_OUTPUT_LOCK.acquire()
    print(STRING)
    GL_OUTPUT_LOCK.release()


def log_exception(EXCEPTION_STR,
                  EXCEPTION_LOG_FILE,
                  EXCEPTION_LOG_FID=None):
    if EXCEPTION_LOG_FID is not None:
        EXCEPTION_LOG_FID.write(EXCEPTION_STR + "\n\n")
        EXCEPTION_LOG_FID.flush()
    else:
        fid = open(EXCEPTION_LOG_FILE, 'a+')
        fid.write(EXCEPTION_STR + "\n")
        fid.close()


def lock_log_exception(GL_EXCEPTION_LOG_FILE, GL_EXCEPTION_LOG_FID, EXC_STR):
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


def fetch_info(ELEM, GL_OUTPUT_FILE, GL_EXCEPTION_LOG_FILE, GL_SCREENSHOT_DIR, BANNER_PATTERNS):
    rank, uri = ELEM
    lock_print("%s => %s [rank: %s]" % (
        str(datetime.now()).split(".")[0], uri, rank))
    try:
        # selenium page loads...
        (page_source, page_title, resources_ordlist, redirection_chain,
         exception, exception_str, browserstart_ts,
         browserend_ts, cookies, banner, screenshot_file) = download_with_browser(
            URL=uri,
            RUN_HEADLESS=GL_browser_RUN_HEADLESS,
            PAGE_LOAD_TIMEOUT=GL_browser_PAGE_LOAD_TIMEOUT,
            CHROMEDRIVER_LOCK=GL_CHROMEDRIVER_LOCK,
            GL_SCREENSHOT_DIR=GL_SCREENSHOT_DIR,
            BANNER_PATTERNS=BANNER_PATTERNS)

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

            dom = url_to_domain(uri)
            source_ip_list = [x[1] for x in recursively_resolve_domain(dom)[0] if x[0] == 'A']
            source_url_info = download_info_using_rdap_cache(IP=source_ip_list[-1]) if len(source_ip_list) > 0 else None

            rdap_res = {
                "rdap_infos_dict": rdap_infos_dict,
                "url_info": source_url_info
            }

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
                RDAP_INFOS_DICT=rdap_res,
                COOKIES=cookies,
                BANNER=banner,
                SCREENSHOT_FILE=screenshot_file
            )
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
                                     RDAP_INFOS_DICT=None,
                                     COOKIES=cookies,
                                     BANNER=banner,
                                     SCREENSHOT_FILE=screenshot_file)

        append_to_file(struct, GL_OUTPUT_FILE)
    except Exception as e:
        ts = str(datetime.now()).split(".")[0]
        exception = str(e).split("\n")[0]
        exception_str = "[%s] Exception: %s\n" % (ts, exception)
        exception_str += "* SCRIPT=integration.py\n"
        exception_str += "** FUNCTION=main\n"
        exception_str += "*** ELEM=%s\n" % (str(ELEM))
        exception_str += "**** %s" % traceback.format_exc()
        lock_log_exception(GL_EXCEPTION_LOG_FILE=GL_EXCEPTION_LOG_FILE, GL_EXCEPTION_LOG_FID=None,
                           EXC_STR=exception_str)


def drop_columns_and_zip(result_file: Path):
    keep_cols = [
        "browser_module.cookies.cookies",
        "browser_module.cookies.request_timestamp",
        "browser_module.banner.banner_detected",
        "browser_module.banner.banner_matched_on",
        "rdap_module.url_info.asn_country_code",
        "rdap_module.url_info.query",
        "source_ip", "browser_module.uri",
        "browser_module.page_source", "browser_module.screenshot_file",
        "domain"
    ]
    df = load_output(result_file, keep_cols=keep_cols)
    zip_out = ".".join(str(result_file).split(".")[:-1]) + ".json.gz"
    lock_print(STRING=f'Selecting sub columns and zipping to {".".join(str(result_file).split(".")[:-1]) + ".json.gz"}')

    lock_print(STRING=f"Writing {len(df.columns)} columns, {len(df)} rows")

    df.to_json(zip_out, compression="gzip")


def main():
    output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                              Path(("../resources/" +
                                    (os.environ.get("OUTPUT_DIR") or
                                     (os.environ.get("VM_LOCATION", "local") + "_"
                                      + time.strftime("output_%Y%m%d-%H%M%S"))
                                     )
                                    ))
                              )
    GL_OUTPUT_DIR = Path(output_dir)
    GL_OUTPUT_DIR.mkdir(exist_ok=True, parents=True)
    GL_OUTPUT_FILE = GL_OUTPUT_DIR / (os.environ.get("VM_LOCATION", '') + "results.jsonl")
    GL_SCREENSHOT_DIR = GL_OUTPUT_DIR / (os.environ.get("VM_LOCATION", '') + "screenshots")
    (GL_SCREENSHOT_DIR / "banner_detected").mkdir(exist_ok=True, parents=True)
    (GL_SCREENSHOT_DIR / "no_banner_detected").mkdir(exist_ok=True, parents=True)
    open(GL_OUTPUT_FILE, 'a+', encoding='utf-8').close()
    # GL_OUTPUT_FID = open(GL_OUTPUT_FILE, 'a', encoding="utf-8")

    GL_EXCEPTION_LOG_FILE = GL_OUTPUT_DIR / "exceptions.log"
    open(GL_EXCEPTION_LOG_FILE, 'a+', encoding='utf-8').close()
    # GL_EXCEPTION_LOG_FID = open(GL_EXCEPTION_LOG_FILE, 'a', encoding='utf-8')

    BANNER_PATTERNS = get_banner_patterns()

    # list of URIs already processed
    GL_PROCESSED_URIS_DICT = get_list_processed_from_json(GL_OUTPUT_FILE)

    rankdomain_list = load_domains_list(FNAME=GL_URI_FILE,
                                        LIMIT=GL_MAX_DOMAINS_TO_CONTACT,
                                        SHUFFLE=GL_SHUFFLE_DOMAINS_LIST)
    # expand expand each string that represents a domain name with the
    # four prefixes: "http://", "http://www.", "https://",
    # "https://www." (in order to generate a valid URL that)
    rankuri_list = expand_with_protocols(rankdomain_list, GL_PROCESSED_URIS_DICT)

    tot_processed = 0
    # process in chunks
    for i in tqdm(range(0, len(rankuri_list), GL_CRAWL_CHUNK_SIZE)):
        lock_print(f"Writing to {GL_OUTPUT_FILE}")
        p = multiprocessing.Pool(GL_MAX_NUM_CHROMEDRIVER_INSTANCES)
        chunk = rankuri_list[i: i + GL_CRAWL_CHUNK_SIZE]
        p.starmap(
            fetch_info,
            [(c, GL_OUTPUT_FILE, GL_EXCEPTION_LOG_FILE, GL_SCREENSHOT_DIR, BANNER_PATTERNS) for c in chunk]
        )
        # p.map(fetch_info, chunk)
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
    drop_columns_and_zip(GL_OUTPUT_FILE)


if __name__ == "__main__":
    main()
