#!/usr/bin/env python
from dns import resolver
import traceback
import time


gl_NAMESERVERS_LIST = [
    "9.9.9.9",  # Quad9 DNS
    "149.112.112.112",  # Quad9 DNS - 2nd nameserver
    "8.8.8.8",  # Google DNS
    "208.67.222.222",  # OpenDNS
    "208.67.220.220",  # OpenDNS
]


class StaleDNSFormatUsed(Exception):
    def __init__(self, rdtype, queried_domain):
        self.rdtype = rdtype
        self.queried_domain = queried_domain

    def __str__(self):
        return "!!!\nqueried_domain: %s\nrdtype: %s\n" % (
            self.rdtype,
            self.queried_domain)


def recursively_resolve_domain(DOMAIN):
    def get_resolver():
        if 'dnsresolver' not in globals():
            global dnsresolver
            dnsresolver = resolver.Resolver(configure=False)
            dnsresolver.nameservers = gl_NAMESERVERS_LIST
        return dnsresolver
    r = get_resolver()
    resolutions = None
    exception = None
    exception_str = None
    start_ts, end_ts = time.time(), time.time()
    try:
        dnsresp = r.query(DOMAIN)
        resolutions = []
        for ans in dnsresp.response.answer:
            # Type 'A'
            if (ans.rdtype == 1) and (" IN A " in ans.to_text()):
                answer_type = "A"
                # Type 'CNAME'
            elif (ans.rdtype == 5) and (" IN CNAME " in ans.to_text()):
                answer_type = "CNAME"
                # Type 'DNAME'
            elif (ans.rdtype == 39) and (" IN DNAME " in ans.to_text()):
                answer_type = "DNAME"
                raise StaleDNSFormatUsed(answer_type, str(ans[0]))
            # Type 'ANAME'
            elif " IN ANAME " in ans.to_text():
                answer_type = "ANAME"
                raise StaleDNSFormatUsed(answer_type, str(ans[0]))
            else:
                continue
            answer_value = str(ans[0])
            resolutions.append((answer_type, answer_value))
    ### All nameservers failed to answer the query
    except Exception as e:
        ts = str(datetime.now()).split(".")[0]
        exception = str(e).split("\n")[0]
        exception_str = "[%s] Exception: %s\n" % (ts, exception)
        exception_str += "* SCRIPT=dns_resolve.py\n"
        exception_str += "** FUNCTION=recursively_resolve_domain\n"
        exception_str += "*** DOMAIN=%s\n" % (DOMAIN)
        exception_str += "**** %s" % traceback.format_exc()
    finally:
        end_ts = time.time()
        return resolutions, exception, exception_str, start_ts, end_ts


if __name__ == "__main__":

    domain = "bitbucket.org"
    print("DOMAIN: %s" % (domain))
    (resolutions, exception,
     exception_str, start_ts, end_ts) = recursively_resolve_domain(domain)
    if exception is None:
        if resolutions is not None:
            for i, elem in enumerate(resolutions):
                answer_type, answer_value = elem
                print("%s- [record type: %s] %s" % (i+1, answer_type,
                                                    answer_value))
        else:
            print("NO ANSWER SECTION FOR DOMAIN %s" % (domain))
    else:
        print("Exception: %s" % exception)
    print("Time spent: %4.2f seconds" % (end_ts - start_ts))
    print()
