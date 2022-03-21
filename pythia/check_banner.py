import json
import re


def iterate_over_websites(output_file):
    res = []
    patterns = ['banner', 'accept cookie', 'cookie consent', 'accept all cookies', 'cookie settings']
    with open(output_file) as file:
        for line in file:
            # add regularExpression
            text = json.loads(line)
            for pattern in patterns:
                elem = text['browser_module']['page_source']
                if re.search(pattern, elem, flags=re.IGNORECASE) and text not in res:
                    res.append(text)
        print(res)


if __name__ == "__main__":
    # first parameter: json result file of running task_manager.py
    # second parameter: uris file with the domains we want to check
    # third parameter: output file path with for each domain if it has a cookie banner or not
    iterate_over_websites("samples/example.json", "samples/uris.csv", "samples/banner_check.csv")
