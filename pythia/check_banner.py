import json
import re


def iterate_over_websites(output_file):
    res = []
    patterns = ['Banner', 'banner']
    with open(output_file) as file:
        for line in file:
            # add regularExpression
            text = json.loads(line)
            for pattern in patterns:
                elem = text['browser_module']['page_source']
                if re.search(pattern, elem) and text not in res:
                    res.append(text)
        print(res)


if __name__ == "__main__":
    iterate_over_websites("samples/example.json")
