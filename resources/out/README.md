# combined_output.json.gz

This describes the output data gathered by querying a list of top domains (of the world and the Netherlands) from 6 different locations in the world, then stacking the results of each run on top of eachother. The result is a Dataframe with 4488 rows (748 domains succesfully queried per country).

## Loading into pandas dataframe:
`df = pd.read_json('combined_output.json.gz', compression='gzip')`

## Column explanations
|    | 0                                        | 1       | 2   |
|---:|:-----------------------------------------|:--------|:----|
|  0 | cookies           | list  | List of cookies    |
|  1 | request_timestamp | float64 | Timestamp of request (epoch seconds)    |
|  2 | banner_detected    | bool    | If a banner was detected or not    |
|  3 | banner_matched_on  | list    | List of phrases the banner was detected on    |
|  4 | source_ip                                | string  | IP of the VM that sent out the request    |
|  5 | uri                       | string  | URI that was queried    |
|  6 | screenshot_file           | string  | Location on VM filesystem of screenshot    |
|  7 | domain                                   | string  | Domain that was queried    |
|  8 | target_ip                                | string  | IP the website is hosted on    |
|  9 | target_ip_country_code                   | string  | Country code of country of target_ip (retrieved using [freegeoip.app](freegeoip.app) 's API)    |
| 10 | target_asn_country_code                  | string  | Country code of ASN the target_ip is registered to    |
| 11 | location                                 | string  | Location the host VM that sent out request is in    |
| 12 | dataset                                  | string  | 'dutch' or 'world' depending on whether the TLD is '.nl' or something else    |