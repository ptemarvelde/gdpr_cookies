import json
from typing import List, Union

import pandas as pd
from tldextract import extract

COOKIE_DURATION_COLUMN = 'duration_s'


def extract_from_rdap_module(url_info: dict):
    return url_info['query'], url_info['asn_country_code']


def load_output(output_file, keep_cols: Union[list, str] = None) -> pd.DataFrame:
    if keep_cols is None:
        keep_cols = [
            'browser_module.exception',
            'browser_module.uri',
            'browser_module.cookies.request_timestamp',
            'browser_module.cookies.cookies',
            'browser_module.screenshot_file',
            'browser_module.banner_detected',
            'domain'
        ]

    with open(output_file, 'r') as f:
        lines = f.read().splitlines()

    df_inter = pd.DataFrame(lines)
    df_inter.columns = ['json_element']

    df_ = pd.json_normalize(df_inter['json_element'].apply(json.loads))

    # TODO extract (base) domain
    df_['domain'] = df_['browser_module.uri'].apply(domain_from_uri)
    df_['browser_module.cookies.cookies'] = df_[
        ['browser_module.cookies.request_timestamp', 'browser_module.cookies.cookies']].apply(calc_cookie_duration,
                                                                                              axis=1)

    # df_['rdap_module.ip'] = df_[['rdap_module.url_info']].apply(lambda x: x['query'], axis=1)
    # df_['rdap_module.country_code'] = df_[['rdap_module.url_info']].apply(lambda x: x['asn_country_code'], axis=1)
    resdf = df_[keep_cols] if keep_cols != 'all' else df_
    return resdf


def calc_cookie_duration(row: pd.Series) -> List[dict]:
    timestamp, cookies = row[0], row[1]
    for cookie in cookies:
        cookie[COOKIE_DURATION_COLUMN] = cookie.get('expiry', timestamp) - timestamp
    return cookies


def domain_from_uri(uri: str) -> str:
    return '.'.join(extract(uri)[-2:])
