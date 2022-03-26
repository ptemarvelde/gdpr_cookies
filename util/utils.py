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
            'domain',
            'host_ip',
            'host_ip_country_code',
            'host_asn_country_code'
        ]

    with open(output_file, 'r') as f:
        lines = f.read().splitlines()

    df_inter = pd.DataFrame(lines)
    df_inter.columns = ['json_element']

    df_ = pd.json_normalize(df_inter['json_element'].apply(json.loads))

    df_['domain'] = df_['browser_module.uri'].apply(domain_from_uri)
    df_['browser_module.cookies.cookies'] = df_[
        ['browser_module.cookies.request_timestamp', 'browser_module.cookies.cookies']].apply(calc_cookie_duration,                                                                                 axis=1)

    df_['target_ip'] = df_['rdap_module.loc_info.ip']
    df_['target_ip_country_code'] = df_['rdap_module.loc_info.country_code']
    df_['target_asn_country_code'] = df_['rdap_module.url_info.asn_country_code']
    resdf = df_[keep_cols] if keep_cols != 'all' else df_
    return resdf


def calc_cookie_duration(row: pd.Series) -> List[dict]:
    timestamp, cookies = row[0], row[1]
    if timestamp and not isinstance(cookies, float):
        for cookie in cookies:
            cookie[COOKIE_DURATION_COLUMN] = cookie.get('expiry', timestamp) - timestamp
    return cookies


def domain_from_uri(uri: str) -> str:
    return '.'.join(extract(uri)[-2:])
