#!/usr/bin/env python
import socket
from datetime import datetime
import ipwhois
import random
import time
import warnings
import traceback
import intervaltree
import multiprocessing
from netaddr import IPNetwork, IPAddress


gl_RDAP_RATE_LIMIT_TIMEOUT = 10
gl_NUM_RDAP_RETRIES = 3
gl_RDAP_CACHE_FRESHNESS = 60*60*24  # 1 day
gl_RDAP_CACHE_LOCK = multiprocessing.Lock()
gl_RDAP_CIDR2TIMESTAMP = {}
gl_RDAP_CACHE_CIDRS = intervaltree.IntervalTree()
gl_RDAP_CACHE_IPS = {}


def download_rdap_info(IP):
    rdap_info = None
    list_exception = []
    list_exception_str = []
    rdap_retries_counter = gl_NUM_RDAP_RETRIES
    start_ts, end_ts = time.time(), time.time()
    if IP:
        while rdap_info is None and rdap_retries_counter > 0:
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=UserWarning)
                    rdap_info = ipwhois.IPWhois(IP).lookup_rdap(
                        rate_limit_timeout=gl_RDAP_RATE_LIMIT_TIMEOUT)
            except ipwhois.exceptions.IPDefinedError as e:
                ts = str(datetime.now()).split(".")[0]
                exception = str(e).split("\n")[0]
                exception_str = "[%s] Exception: %s\n" % (ts, exception)
                exception_str += "* SCRIPT=rdap_query.py\n"
                exception_str += "** FUNCTION=download_rdap_info\n"
                exception_str += "*** IP=%s\n" % (IP)
                exception_str += "**** %s" % traceback.format_exc()
                list_exception.append(exception)
                list_exception_str.append(exception_str)
                # store in the result for the rdap_info, as we will
                # not query again for this IP
                rdap_info = {"raw": exception}
            except ipwhois.exceptions.HTTPRateLimitError as e:
                r = random.randint(60, 90)
                ts = str(datetime.now()).split(".")[0]
                exception = str(e).split("\n")[0]
                exception_str = "[%s] Exception: %s\n" % (ts, exception)
                exception_str += "* SCRIPT=rdap_query.py\n"
                exception_str += "** FUNCTION=download_rdap_info\n"
                exception_str += "*** IP=%s" % (IP)
                exception_str += "**** sleep_time: %s\n" % (r)
                exception_str += "**** rdap_retries_counter: %s\n" % (
                    rdap_retries_counter)
                exception_str += "***** %s" % traceback.format_exc()
                list_exception.append(exception)
                list_exception_str.append(exception_str)
                time.sleep(r)
            except ipwhois.exceptions.HTTPLookupError as e:
                r = random.randint(10, 20)
                ts = str(datetime.now()).split(".")[0]
                exception = str(e).split("\n")[0]
                exception_str = "[%s] Exception: %s\n" % (ts, exception)
                exception_str += "* SCRIPT=rdap_query.py\n"
                exception_str += "** FUNCTION=download_rdap_info\n"
                exception_str += "*** IP=%s" % (IP)
                exception_str += "**** sleep_time: %s\n" % (r)
                exception_str += "**** rdap_retries_counter: %s\n" % (
                    rdap_retries_counter)
                exception_str += "***** %s" % traceback.format_exc()
                list_exception.append(exception)
                list_exception_str.append(exception_str)
                time.sleep(r)
                rdap_retries_counter -= 1
            except Exception as e:
                ts = str(datetime.now()).split(".")[0]
                exception = str(e).split("\n")[0]
                exception_str = "[%s] Exception: %s\n" % (ts, exception)
                exception_str += "* SCRIPT=rdap_query.py\n"
                exception_str += "** FUNCTION=download_rdap_info\n"
                exception_str += "*** IP=%s" % (IP)
                exception_str += "**** %s" % traceback.format_exc()
                list_exception.append(exception)
                list_exception_str.append(exception_str)
                break
    if len(list_exception) == 0:
        list_exception = None
    if len(list_exception_str) == 0:
        list_exception_str = None
    end_ts = time.time()
    return rdap_info, list_exception, list_exception_str, start_ts, end_ts


def download_info_using_rdap_cache(IP):
    def ts_is_valid(PREFIX):
        if PREFIX in gl_RDAP_CIDR2TIMESTAMP:
            now = time.time()
            ts_fetched = gl_RDAP_CIDR2TIMESTAMP[PREFIX]
            return (time.time() - ts_fetched) < gl_RDAP_CACHE_FRESHNESS
        return False

    def extract_cidr_from_rdapinfo(RDAP_INFO):
        cidr = None
        if RDAP_INFO is not None and \
           "network" in rdap_info and \
           "cidr" in RDAP_INFO["network"]:
            cidr = rdap_info["network"]["cidr"]
            # We have a format with more than one range, such as
            # "cidr/XX, cidr/YY"
            if "," in cidr:
                cidr_list = [el.strip().split("/")
                             for el in cidr.split(",")]
                # sort the list with the "most specific prefix at the
                # beginning"
                cidr_list = sorted(cidr_list, key=lambda t: int(t[1]),
                                   reverse=True)
                # and use this prefix as CIDR
                cidr = "%s/%s" % (cidr_list[0][0], cidr_list[0][1])
        return cidr

    # The 'gl_RDAP_CACHE_CIDRS' structure is an interval tree which
    # does *not* allow null-range intervals; for thi reason we will
    # use a dedicated ditionary, 'gl_RDAP_CACHE_IPS' where we store
    # ranges that consist of a single IP address.
    cache_hit = False
    start_ts = time.time()
    end_ts = start_ts
    # First we check if we can find the IP in the cache of
    # 'singletons' where each ranges consist of only one IP address.
    if gl_RDAP_CACHE_LOCK is not None:
        gl_RDAP_CACHE_LOCK.acquire()
    if IP in gl_RDAP_CACHE_IPS:
        # convert the IP into a '/32' prefix
        cidr = "%s/32" % (IP)
        if ts_is_valid(cidr):
            (rdap_info, list_exception,
             list_exception_str) = gl_RDAP_CACHE_IPS[IP]
            cache_hit = True
    if gl_RDAP_CACHE_LOCK is not None:
        gl_RDAP_CACHE_LOCK.release()
    # In case we did not have a cache hit, we will search for the IP
    # in the cache that contains ranges of IP addreesses.
    if cache_hit is False:
        int_ip = IPNetwork(IP).first
        if gl_RDAP_CACHE_LOCK is not None:
            gl_RDAP_CACHE_LOCK.acquire()
        elems = list(gl_RDAP_CACHE_CIDRS[int_ip])
        if gl_RDAP_CACHE_LOCK is not None:
            gl_RDAP_CACHE_LOCK.release()
        # in case we find more that one range in the cache
        # that would be appropriate for this IP
        if len(elems) > 1:
            list_elems = [(e, e.end-e.begin) for e in elems]
            # we sort ranges and we choose the SMALLEST one
            list_elems = sorted(list_elems, key=lambda el: el[1])
            elems = [list_elems[0][0]]
        # if we find a corresponding range in the cache that includes IP
        if len(elems) == 1:
            (rdap_info, list_exception,
             list_exception_str) = elems[0].data
            cidr = extract_cidr_from_rdapinfo(rdap_info)
            if cidr is not None and ts_is_valid(cidr):
                cache_hit = True
    if cache_hit is False:
        # first we query RDAP for this IP
        (rdap_info, list_exception,
         list_exception_str, start_ts,
         end_ts) = download_rdap_info(IP)
        # then we have to update the cache with the new range
        cidr = extract_cidr_from_rdapinfo(rdap_info)
        if cidr is not None:
            ipnet = IPNetwork(cidr)
            range_start = ipnet.first
            range_end = ipnet.last
            if gl_RDAP_CACHE_LOCK is not None:
                gl_RDAP_CACHE_LOCK.acquire()
            if range_start != range_end:
                gl_RDAP_CACHE_CIDRS[range_start:range_end] = (
                    rdap_info, list_exception, list_exception_str)
            else:
                gl_RDAP_CACHE_IPS[IP] = (rdap_info,
                                         list_exception,
                                         list_exception_str)
            gl_RDAP_CIDR2TIMESTAMP[cidr] = time.time()
            if gl_RDAP_CACHE_LOCK is not None:
                gl_RDAP_CACHE_LOCK.release()
    return (rdap_info, list_exception, list_exception_str, start_ts, end_ts,
            cache_hit)


if __name__ == "__main__":

    import json

    ip = "8.8.8.8"
    (rdap_info, list_exception,
     list_exception_str, start_ts, end_ts,
     cache_hit) = download_info_using_rdap_cache(ip)
    print("IP: %s" % (ip))
    print("cache_hit: %s" % (cache_hit))
    if rdap_info is not None:
        print(json.dumps(rdap_info, indent=2))
    else:
        for i, elem in enumerate(list_exception):
            print("Exception-%s:" % (i))
            print(elem)
    print("Time spent: %4.2f seconds" % (end_ts - start_ts))
