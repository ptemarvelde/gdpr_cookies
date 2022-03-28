import sys
sys.path.append("../")
from pythia.banner_config import get_banner_patterns, lib_js_file_names
import pandas as pd
from bs4 import BeautifulSoup
import re 
import os 
import logging
import json 

logging.getLogger().setLevel(os.environ.get("DRIVER_LOG_LEVEL", "INFO"))

def detect_banner(page_html, banner_patterns, url='') -> dict:
    # delete all content with <noscript> tags, if they exist
    if page_html:
        html = BeautifulSoup(page_html, "html.parser")
        noscript_tag = html.select('noscript')
        if noscript_tag:
            for s in noscript_tag:
                s.extract()
        page_html = str(html)

    # detecting banner
    banner_matched_keywords = detect_banner_keywords(page_html, banner_patterns)
    matched_patterns = detect_banner_cookie_libs(page_html)
    banner_matched_keywords.extend(matched_patterns)

    banner_dict = {
        'url': url,
        'banner_detected': len(banner_matched_keywords) > 0,
        'banner_matched_on': banner_matched_keywords,
    }

    return banner_dict


def detect_banner_keywords(page_html, banner_patterns) -> list:
    banner_matched_keywords = []
    if page_html:
        logging.debug(f"First 100 chars in page html: {page_html[:100]}")
        for pattern in banner_patterns:
            logging.debug(f'pattern: {pattern}')
            if re.search(pattern, page_html, flags=re.IGNORECASE):
                banner_matched_keywords.append(pattern)
    return banner_matched_keywords


def detect_banner_cookie_libs(page_source) -> list:
    matched_patterns = []
    if page_source:
        for pattern in lib_js_file_names:
            if re.search(pattern, page_source, flags=re.IGNORECASE):
                matched_patterns += [pattern]
    return matched_patterns


if __name__ == '__main__':
    df = pd.read_json('./californiaresults.json')

    df_src = df['browser_module.page_source']
    df_uri = df['browser_module.uri']

    banner_patters = get_banner_patterns()

    with open('./offline_banner_detection.txt', 'w') as f:
        for idx in range(len(df)):
            f.write(json.dumps(detect_banner(df_src[idx], banner_patters, url=df_uri[idx]), default=str) + '\n')
