import os
import time
from io import StringIO
from pathlib import Path
from typing import Tuple

import pandas as pd
import requests
from tldextract import tldextract


def get_domains() -> Tuple[pd.DataFrame, pd.DataFrame]:
    response = requests.get("https://tranco-list.eu/download/L294/200000")
    df = pd.read_csv(StringIO(response.text), header=None, index_col=0, names=['domain'])
    df['tld'] = df['domain'].apply(lambda d: tldextract.extract(d).suffix)
    df['nl'] = df['tld'] == 'nl'
    return df[df['nl'] == True], df[df['nl'] == False]


def get_and_write_domains(target_dir: str, dutch_limit: int = 50, world_limit: int = 500) -> None:
    target_dir = Path(target_dir) \
                 # / time.strftime("%Y%m%d-%H%M%S")
    target_dir.mkdir(parents=True, exist_ok=True)
    dutch_df, world_df = get_domains()
    write_domain_df_to_csv(dutch_df[:dutch_limit], target_dir / f'dutch_top_{dutch_limit}.csv')
    write_domain_df_to_csv(world_df[:world_limit], target_dir / f'world_top_{world_limit}.csv')


def write_domain_df_to_csv(df_: pd.DataFrame, file: Path) -> None:
    df = df_.copy()
    df = df.reset_index()
    df.index += 1
    df.domain.to_csv(file, index=True, header=False)


if __name__ == '__main__':
    get_and_write_domains('../resources/data', dutch_limit=50, world_limit=500)
