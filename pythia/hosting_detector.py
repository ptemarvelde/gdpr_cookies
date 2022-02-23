#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urllib.parse import urlparse
import json
from collections import OrderedDict
import sys
from check_ownership import *
import socket


GL_PRINT_ON_STDOUT = True
GL_PREPROCESSED_JSON_DATA = "./samples/example.json"
GL_OUTPUT_CVS_FILE = "./samples/example_hosting.csv"

RDAP_USED_FIELDS_MAPPING = {
    # ASN
    "asn": False,  # str
    "asn_description": True,  # str
    "asn_cidr": False,  # str
    "asn_country_code": False,  # str
    # Network
    "network_netname": False,  # str
    "network_remark_list": True,  # list
    # Objects
    "object_email_list": True,  # list
    "object_address_list": True,  # list
    "object_kind_list": False,  # list
    "object_name_list": True,  # list
    "object_remark_list": True,  # list
}


def check_if_ip(DOMAIN):
    try:
        domain = DOMAIN
        if domain.endswith("."):
            domain = domain[:-1]
        socket.inet_aton(domain)
        return True
    except socket.error:
        return False


def cleanup_characters(STR):
    return STR.replace("\r\n", " ").replace("\n", " ").replace(
        ",", "").replace("!", "").replace(";", "").strip()  # .lower()


def filter_short_tokens(LIST):
    return filter(lambda x: x if len(x) > 3 else None, LIST)


def extract_focusdata(RDAP_INFO):
    if RDAP_INFO:
        focusdata = OrderedDict()
        for key in ["asn", "asn_description", "asn_cidr", "asn_country_code"]:
            try:
                focusdata[key] = (
                    RDAP_USED_FIELDS_MAPPING[key], RDAP_INFO[key])
            except KeyError:
                focusdata[key] = (
                    RDAP_USED_FIELDS_MAPPING[key], None)
        # network_netname
        try:
            focusdata['network_netname'] = (
                RDAP_USED_FIELDS_MAPPING["network_netname"],
                RDAP_INFO['network']['name'])
        except KeyError:
            focusdata['network_netname'] = (
                RDAP_USED_FIELDS_MAPPING["network_netname"], None)
        # network_remark
        try:
            network_remarks_set = set([])  # we could have duplicates
            for net_rmk_dict in RDAP_INFO['network']['remarks']:
                network_remark = ""
                for key in ["title", "description", "links"]:
                    if net_rmk_dict[key] is not None:
                        network_remark += "%s " % (net_rmk_dict[key])
                network_remark = cleanup_characters(network_remark)
                network_remarks_set.add(network_remark)
            network_remark_list = list([el for el in network_remarks_set])
            # store in the dictionary
            focusdata['network_remark_list'] = (
                RDAP_USED_FIELDS_MAPPING["network_remark_list"],
                network_remark_list)
        except (KeyError, TypeError):
            focusdata['network_remark_list'] = (
                RDAP_USED_FIELDS_MAPPING["network_remark_list"], None)
        address_set = set([])
        email_set = set([])
        kind_set = set([])
        name_set = set([])
        remark_set = set([])
        if 'objects' in RDAP_INFO:
            for value in RDAP_INFO['objects'].values():
                if value['contact'] is not None:
                    contact = value['contact']
                    if 'address' in value['contact'] and \
                       contact['address'] is not None:
                        addresses = [
                            cleanup_characters(a["value"]) for a in
                            contact['address'] if a["value"] is not None]
                        addresses = filter_short_tokens(addresses)
                        addresses = " ".join([elem for elem in addresses])
                        if len(addresses) > 0:
                            address_set.add(addresses)
                    if 'email' in contact and \
                       contact['email'] is not None:
                        emails = " ".join([
                            "@"+cleanup_characters(e["value"]).split("@")[1]
                            for e in contact['email']
                            if e["value"] is not None and "@" in e["value"]])
                        if len(emails) > 0:
                            email_set.add(emails)
                    if 'kind' in contact and \
                       contact['kind'] is not None:
                        kind = cleanup_characters(contact['kind'])
                        if len(kind) > 0:
                            kind_set.add(kind)
                    if 'name' in contact and \
                       contact['name'] is not None:
                        name = cleanup_characters(contact['name'])
                        if len(name) > 0:
                            name_set.add(name)
                if value['remarks'] is not None:
                    remarks = value['remarks']
                    object_remark = ""
                    for obj_rmk_dict in remarks:
                        for key in ["title", "description"]:
                            if obj_rmk_dict[key] is not None:
                                object_remark += "%s " % (obj_rmk_dict[key])
                        if obj_rmk_dict["links"] is not None:
                            for l in obj_rmk_dict["links"]:
                                object_remark += "%s " % (l)
                    if len(object_remark) > 0:
                        object_remark = cleanup_characters(object_remark)
                        remark_set.add(object_remark)
        address_list = list(address_set) if len(address_set) > 0 else None
        email_list = list(email_set) if len(email_set) > 0 else None
        kind_list = list(kind_set) if len(kind_set) > 0 else None
        name_list = list(name_set) if len(name_set) > 0 else None
        remark_list = list(remark_set) if len(remark_set) > 0 else None
        focusdata['object_email_list'] = (
            RDAP_USED_FIELDS_MAPPING["object_email_list"], email_list)
        focusdata['object_address_list'] = (
            RDAP_USED_FIELDS_MAPPING["object_address_list"], address_list)
        focusdata['object_kind_list'] = (
            RDAP_USED_FIELDS_MAPPING["object_kind_list"], kind_list)
        focusdata['object_name_list'] = (
            RDAP_USED_FIELDS_MAPPING["object_name_list"], name_list)
        focusdata['object_remark_list'] = (
            RDAP_USED_FIELDS_MAPPING["object_remark_list"], remark_list)
        return focusdata
    else:
        return None


def load_from_file(FNAME):
    fid = open(FNAME, 'r')
    for row in fid:
        yield json.loads(row)
    fid.close()


def url_parse_scheme_domain_port(URL):
    # Given an URL in input, returns in output:
    # - the scheme
    # - the domain
    # - the port
    parsedurl = urlparse(URL)
    scheme = parsedurl.scheme
    domain = parsedurl.netloc
    port = None
    if parsedurl.port is not None:
        domain = domain.split(":")[0]
    return scheme, domain, port


def process_struct(DOMAIN,
                   STRUCT,
                   INDENT_SPACES=8,
                   FILTER_ON_ROOT_DOMAIN=False):
    out_info = OrderedDict()
    page_title = STRUCT["browser_module"]["page_title"]
    page_source = STRUCT["browser_module"]["page_source"]
    redirection_chain = STRUCT["browser_module"]["redirection_chain"]
    exception = STRUCT["browser_module"]["exception"]
    urls = [elem[0] for elem in STRUCT["browser_module"]["resources_ordlist"]]
    dns = dict([(elem["domain"], elem) for elem in STRUCT["dns_module"]])
    ips = dict([(elem["ip"], elem["rdap_info"])
                for elem in STRUCT["rdap_module"]])
    if exception is None and redirection_chain is not None:
        landing_page = redirection_chain[-1]
        (lp_scheme, lp_domain,
         lp_port) = url_parse_scheme_domain_port(landing_page)
        # generate a dictionary of unique domains (extracte from the
        # visited URLs)
        domains_to_urls_dict = {}
        for u in urls:
            scheme, domain, port = url_parse_scheme_domain_port(u)
            # we keep only those for which the DNS resolution succeeded
            if domain in dns:
                if domain not in domains_to_urls_dict:
                    domains_to_urls_dict[domain] = [0, 0]
                # extract the scheme
                if scheme == "http":
                    domains_to_urls_dict[domain][0] += 1
                elif scheme == "https":
                    domains_to_urls_dict[domain][1] += 1
                else:
                    # unsupported protocl
                    continue
        # sort the domains depending on the number of URLs with that
        # domain
        tmp = [(v[0]+v[1], k) for k, v in domains_to_urls_dict.items()]
        tmp.sort(reverse=True)
        # and put at the beginning the domain of the 'landing_page'
        pos = [i for i, el in enumerate(tmp) if el[1] == lp_domain]
        if len(pos) > 0:
            pos = pos[0]
            el = tmp.pop(pos)
            tmp.insert(0, el)
            domains_to_urls_dict_ordered = OrderedDict()
            for tot_urls, domain in tmp:
                domains_to_urls_dict_ordered[domain] = domains_to_urls_dict[
                    domain]
            if len(domains_to_urls_dict_ordered) > 0:
                if FILTER_ON_ROOT_DOMAIN is True:
                    tot_unique_domains = 1
                else:
                    tot_unique_domains = len(domains_to_urls_dict_ordered)
                # process the DNS data
                for domain, v in domains_to_urls_dict_ordered.items():
                    tot_http_urls, tot_https_urls = v
                    tot_unique_domains -= 1
                    out_info[domain] = {
                        "ip_str": None,
                        "dns": None,
                        "dns_exception": None,
                        "ip": None,
                        "ip_exception": None,
                        "self-hosted": None,
                        "hosting_analysis": None,
                        "text": None
                    }
                    # header block
                    text_header = " " * INDENT_SPACES
                    text_header += "└─> " if tot_unique_domains == 0 \
                        else "|─> "
                    text_header += "%s URLs @ %s (HTTP: %s ; HTTPS: %s)\n" % (
                        tot_http_urls + tot_https_urls, domain,
                        tot_http_urls, tot_https_urls)
                    # DNS block
                    dnsinfo = dns[domain]["resolutions"]
                    dnsexception = dns[domain]["exception"]
                    dnsexception_str = dns[domain]["exception_str"]
                    if dnsexception is not None:
                        text_dns = " " * INDENT_SPACES
                        text_dns += "└─> " if tot_unique_domains == 0 \
                            else "|─> "
                        text_dns += "[Exception] %s" % (dnsexception)
                        out_info[domain]["dns_exception"] = dnsexception
                        out_ips = None
                    elif dnsinfo is not None:
                        text_dns = ""
                        l_dns = len(str(tot_http_urls + tot_https_urls)) + 11
                        text_ips = ""
                        out_info[domain]["dns"] = []
                        for rec_type, rec_ans in dnsinfo:
                            text_dns += " " * INDENT_SPACES
                            text_dns += " " if tot_unique_domains == 0 else "|"
                            text_dns += " " * l_dns
                            text_dns += "└─> "
                            if rec_type == "CNAME":
                                text_dns += "[cname] "
                                l_dns += 7+5
                            elif rec_type == "A":
                                text_dns += "[IP] "
                                l_dns += 7+2
                            text_dns += rec_ans + "\n"
                            out_info[domain]["ip_str"] = rec_ans
                            # add structured info
                            out_info[domain]["dns"].append(rec_ans)
                            # IP/RDAP block
                            if check_if_ip(rec_ans):
                                rdap_info = ips[rec_ans]
                                focusdata = extract_focusdata(rdap_info)
                                if focusdata is not None:
                                    out_info[domain]["ip"] = {}
                                    # we need this info to know when to
                                    # use the 'bended arrow'...
                                    to_process = len([
                                        v[0] for v in focusdata.values()
                                        if v[0] is True and v[1] is not None])
                                    for key in ["network_netname",
                                                "network_remark_list",
                                                "object_name_list",
                                                "object_email_list",
                                                "object_address_list",
                                                "object_remark_list",
                                                "asn",
                                                "asn_description",
                                                "asn_cidr",
                                                "asn_country_code"]:
                                        used, value = focusdata[key]
                                        if used is True:
                                            if value is not None:
                                                to_process -= 1
                                                if to_process == 0:
                                                    arrow = "└=>"
                                                else:
                                                    arrow = "|=>"
                                                out_info[domain]["ip"][
                                                    key] = value
                                                if type(value) is list:
                                                    for pos, el in enumerate(
                                                            value, 1):
                                                        text_ips += " " * INDENT_SPACES
                                                        text_ips += " " if tot_unique_domains == 0 else "|"
                                                        text_ips += " " * l_dns + "%s [%s_#%s] %s\n" % (arrow, key, pos, el)
                                                else:
                                                    text_ips += " " * INDENT_SPACES
                                                    text_ips += " " if tot_unique_domains == 0 else "|"
                                                    text_ips += " " * l_dns + "%s [%s] %s\n" % (arrow, key, value)
                    text = text_header
                    text += text_dns
                    text += text_ips[:-1]
                    out_info[domain]["text"] = text
                    hosting_analysis = test_owneship(DOMAIN, page_title, focusdata)
                    if hosting_analysis is not None:
                        self_hosted = sum([len(hosting_analysis[0]),
                                           len(hosting_analysis[1]),
                                           len(hosting_analysis[2]),
                                           len(hosting_analysis[3]),
                                           hosting_analysis[4][2]
                                           if hosting_analysis[4][2] is not None else 0,
                                           hosting_analysis[5][2]
                                           if hosting_analysis[5][2] is not None else 0]) > 0
                    else:
                        self_hosted = None
                    out_info[domain]["hosting_analysis"] = hosting_analysis
                    out_info[domain]["self-hosted"] = self_hosted
        else:
            # did NOT succeed connecting to the URI of the landing_page...
            if exception is None:
                exception = "Landing URI %s not loaded correctly" % (
                    redirection_chain[-1])
            page_title = None
            redirection_chain = None
            out_info[domain] = {
                "dns": None,
                "dns_exception": None,
                "ip": None,
                "ip_exception": None,
                "self-hosted": None,
                "hosting_analysis": None,
                "text": None}
    return exception, page_title, out_info, redirection_chain


def debug_print(HOSTING_ANALYSIS_LIST):
    out = ""
    for i, k in enumerate([
            "domain_in_rdap",
            "rdap_in_domain",
            "title_in_rdap",
            "rdap_in_title",
            "domain_tokenized_intersection_rdap",
            "title_tokenized_intersect_rdap",
            "domain_tokenized_lcs_rdap",
            "title_tokenized_lcs_rdap"]):
        out += "%s: %s\n" % (k, HOSTING_ANALYSIS_LIST[i])
    out += "\n"
    return out


def main():
    whitebold = "\033[1m"
    yellow = "\033[33m"
    marker = "\033[1m\033[34m|\033[m"
    lightgreen = "\033[1m\033[92m"
    redhighligh = "\033[41m"
    default = "\033[m"

    generator = load_from_file(GL_PREPROCESSED_JSON_DATA)
    outfile = open(GL_OUTPUT_CVS_FILE, 'a')
    outfile.write("#inspected_URL,landing_URL,self_hosted\n")

    for i, data_dict in enumerate(generator):
        uri = data_dict["browser_module"]["uri"]
        scheme, domain, port = url_parse_scheme_domain_port(uri)
        if uri is not None:
            (exception, page_title, out_info,
             redirection_chain) = process_struct(DOMAIN=domain,
                                                 STRUCT=data_dict,
                                                 INDENT_SPACES=8,
                                                 FILTER_ON_ROOT_DOMAIN=True)
            if exception is None:
                if GL_PRINT_ON_STDOUT:
                    stdout = "%s) %s%s%s" % (i,
                                             whitebold,
                                             uri,
                                             default)
                    if len(redirection_chain) > 1:
                        stdout += " ~~~> %s%s%s\n" % (whitebold,
                                                      redirection_chain[-1],
                                                      default)
                        redirection_chain_str = " ~> ".join([
                            r for r in redirection_chain])
                        stdout += "[redirection_chain] %s%s%s" % (
                            redhighligh,
                            redirection_chain_str,
                            default)
                    if redirection_chain is not None:
                        (scheme, inspected_domain,
                         port) = url_parse_scheme_domain_port(
                             redirection_chain[-1])
                    else:
                        inspected_domain = None
                    stdout += "\n"
                    stdout += "[inspected_domain] %s\n" % (inspected_domain)
                    stdout += "[title] %s%s%s%s%s" % (marker,
                                                      lightgreen,
                                                      page_title,
                                                      default,
                                                      marker)
                    if GL_PRINT_ON_STDOUT:
                        print(stdout)
                    for k, v in out_info.items():
                        text = v["text"]
                        if GL_PRINT_ON_STDOUT:
                            print(text)
                        break
                    if GL_PRINT_ON_STDOUT:
                        print()
                    # checking self-hosting
                    for k, v in out_info.items():
                        self_hosted_out = "self-hosted: "
                        if v["self-hosted"] is True:
                            self_hosted_out += "%s%s%s\n" % (
                                yellow, v["self-hosted"], default)
                            self_hosted_out += debug_print(
                                v["hosting_analysis"])
                        else:
                            self_hosted_out += "%s\n" % (v["self-hosted"])
                            self_hosted = v["self-hosted"]
                        print(self_hosted_out)
                        break
            else:
                if GL_PRINT_ON_STDOUT:
                    print("%s://%s" % (scheme, domain))
                    print("└─> [%sException%s] %s" % (
                        redhighligh, default, exception))
            if GL_PRINT_ON_STDOUT:
                print()
            landing_page = redirection_chain[-1] \
                if redirection_chain is not None else None
            # write in output file
            outfile.write("%s,%s,%s\n" % (uri, landing_page, self_hosted))
    outfile.flush()
    outfile.close()


if __name__ == "__main__":

    main()
