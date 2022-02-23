#!/usr/bin/evn python
import json


def get_list_processed_from_json(FNAME):
    """Extract URLs from the 'json' that contains all the data"""
    fid = open(FNAME, 'r')
    try:
        uris = set([json.loads(row)["browser_module"]["uri"] for row in fid])
    except json.decoder.JSONDecodeError:
        uris = set([])
    fid.close()
    return uris


if __name__ == "__main__":

    # Example
    fname_json = "./samples/example.json"
    dict_processed_uris = get_list_processed_from_json(fname_json)
