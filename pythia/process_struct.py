#!/usr/bin/env python
import json

def generate_struct(SOURCE_IP,
                    URI,
                    # browser
                    PAGE_SOURCE, PAGE_TITLE,
                    RESOURCES_ORDLIST, REDIRECTION_CHAIN,
                    EXCEPTION, EXCEPTION_STR,
                    BROWSERSTART_TS, BROWSEREND_TS,
                    # dns
                    UNIQUE_DOMAINS_RESOLUTIONS,
                    # rdap
                    RDAP_INFOS_DICT):
    browser_module = {
        "uri": URI,
        "page_source": PAGE_SOURCE,
        "page_title": PAGE_TITLE,
        "resources_ordlist": RESOURCES_ORDLIST,
        "redirection_chain": REDIRECTION_CHAIN,
        "exception": EXCEPTION,
        "exception_str": EXCEPTION_STR,
        "start_ts": BROWSERSTART_TS,
        "end_ts": BROWSEREND_TS
    }
    if UNIQUE_DOMAINS_RESOLUTIONS is not None:
        dns_module = []
        for k, v in UNIQUE_DOMAINS_RESOLUTIONS.items():
            domain = k
            # Those entries were obtained from:
            # dns_module.py -> recursively_resolve_domain(...)
            (resolutions, exception, exception_str, start_ts, end_ts) = v
            dns_entry = {
                "domain": domain,
                "resolutions": resolutions,
                "exception": exception,
                "exception_str": exception_str,
                "start_ts": start_ts,
                "end_ts": end_ts
            }
            dns_module.append(dns_entry)
    else:
        dns_module = None
    if RDAP_INFOS_DICT is not None:
        rdap_module = []
        for k, v in RDAP_INFOS_DICT.items():
            ip = k
            # Those entries were obtained from:
            # rdap_query.py -> download_info_using_rdap_cache(...)
            (rdap_info, list_exception, list_exception_str, start_ts, end_ts,
             cache_hit) = v
            rdap_entry = {
                "ip": ip,
                "rdap_info": rdap_info,
                "list_exception": list_exception,
                "list_exception_str": list_exception_str,
                "start_ts": start_ts,
                "end_ts": end_ts,
                "cache_hit": cache_hit,
            }
            rdap_module.append(rdap_entry)
    else:
        rdap_module = None
    page_struct = {
        "source_ip": SOURCE_IP,
        "browser_module": browser_module,
        "dns_module": dns_module,
        "rdap_module": rdap_module
    }
    return page_struct


def extract_struct(STRUCT):
    source_ip = STRUCT["source_ip"]
    browser_module = STRUCT["browser_module"]
    uri = browser_module["uri"]
    if (browser_module["exception"] is not None) or \
       (browser_module["resources_ordlist"] is None):
        browser_module = None
        dns_module = None
        rdap_module = None
    else:
        dns_module = STRUCT["dns_module"]
        rdap_module = STRUCT["rdap_module"]
    return source_ip, uri, browser_module, dns_module, rdap_module
