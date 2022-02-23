#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import tldextract
from nltk.corpus import stopwords
from wordsegment import load, segment


# load the dictionaries in order to be able to use "segment(...)"
load()
nltk_stopwords = set(stopwords.words('english'))


def cleanup_characters_lower(STR):
    return re.sub("[^a-zA-Z0-9_ ]", "", STR).lower().strip()


def filter_stopwords(LIST):
    return filter(lambda x: (x not in nltk_stopwords) and len(x) > 2, LIST)


def check_intersection(A_SET, LIST_OF_SETS):
    if A_SET is not None and len(A_SET) > 0:
        tmp = [A_SET.intersection(s) for s in LIST_OF_SETS]
        tmp = [(len(elem), elem) for elem in tmp]
        if len(tmp) > 0:
            tmp.sort(reverse=True)
            if tmp[0][0] > 0:
                common_perc = round(1.0*tmp[0][0]/len(A_SET), 1)
                # we require to have 50% or more common tokens
                if common_perc >= 0.5:
                    return (tmp[0][0], tmp[0][1], common_perc)
    return (0, None, None)


def check_longest_common_subsublist(A_LIST, LIST_OF_LISTS):
    def check_longest_common_sublist(LIST1, LIST2):
        cont = 0
        longest_common_substring = None
        lenl1 = len(LIST1)
        lenl2 = len(LIST2)
        for i, el1 in enumerate(LIST1):
            el1 = el1.strip()
            if len(el1.strip()) > 1:
                # we find all the occurences that have "el1" as prefix
                for j in [index for index, el2 in enumerate(LIST2)
                          if el2.startswith(el1)]:
                    cont_new = 1
                    i_next = i + 1
                    j_next = j + 1
                    # keep processing the elements as long as they are in the
                    # same relative positions in the two lists and
                    # "LIST2[j_next]" has "LIST1[i_next]" as prefix (idea: we
                    # want to get rid of punctuation and extra characters)
                    while (i_next < lenl1) and \
                          (j_next < lenl2) and \
                          (LIST2[j_next].startswith(LIST1[i_next])):
                        cont_new += 1
                        i_next += 1
                        j_next += 1
                    if cont_new > cont:
                        cont = cont_new
                        longest_common_substring = LIST1[i:i_next]
        return cont, longest_common_substring
    if A_LIST is not None and len(A_LIST) > 0:
        tmp = [check_longest_common_sublist(A_LIST, elem) for elem in
               LIST_OF_LISTS]
        if len(tmp) > 0:
            tmp.sort(reverse=True)
            if tmp[0][0] > 0:
                return (tmp[0][0],
                        tmp[0][1],
                        round(1.0*tmp[0][0]/len(A_LIST), 1))
    return (0, None, None)


def test_owneship(DOMAIN, TITLE, RDAP_DICT):
    if (DOMAIN is None and TITLE is None) or \
       RDAP_DICT is None:
        return None
    TITLE = TITLE.strip()
    TITLE = cleanup_characters_lower(TITLE)
    # rdap fields that are effectively used
    used_rdap_fields = [v[1] for v in RDAP_DICT.values() if v[0] is True]
    used_rdap_fields_str = []
    for l in used_rdap_fields:
        if l is not None:
            if type(l) is list:
                for ll in l:
                    ll = cleanup_characters_lower(ll)
                    used_rdap_fields_str.append(ll)
            else:
                l = cleanup_characters_lower(l)
                used_rdap_fields_str.append(l)
    used_rdap_fields_str = filter_stopwords(used_rdap_fields_str)
    # used rdap fields tokenized and converted into a "list of lists"
    used_rdap_fields_ll = [filter_stopwords(s.split(" "))
                           for s in used_rdap_fields_str]
    # used rdap fields tokenized and converted into a "list of sets"
    used_rdap_fields_ls = [set(l) for l in used_rdap_fields_ll]
    # effective second level domain domain without the TLD
    domainnotld = tldextract.extract(DOMAIN).domain
    domainnotld = cleanup_characters_lower(domainnotld)
    # domain tokenized (list)
    domain_tokenized_l = segment(domainnotld)
    domain_tokenized_l = filter_stopwords(domain_tokenized_l)
    # domain tokenized (set)
    domain_tokenized_s = set(domain_tokenized_l)
    # title HTTP tokenized (list)
    if TITLE is None or len(TITLE) == 0:
        title_tokenized_l = []
    else:
        title_tokenized_l = [cleanup_characters_lower(el)
                             for el in TITLE.split(" ")]
        title_tokenized_l = filter_stopwords(title_tokenized_l)
    # title HTTP tokenized (set)
    title_tokenized_s = set(title_tokenized_l)

    # The checks.
    ##  1) domainnotld in RDAP
    domain_in_rdap = [el for el in used_rdap_fields_str
                      if len(domainnotld) > 2 and domainnotld in el]

    ##  2) RDAP in domainnotld
    rdap_in_domain = [el for el in used_rdap_fields_str
                      if len(el) > 2 and el in domainnotld]

    ## 3) TITLE in RDAP
    if TITLE is None or len(TITLE) == 0:
        title_in_rdap = []
    else:
        title_in_rdap = [el for el in used_rdap_fields_str
                         if TITLE in el]

    ## 4) RDAP in TITLE
    if TITLE is None or len(TITLE) == 0:
        rdap_in_title = []
    else:
        rdap_in_title = [el for el in used_rdap_fields_str
                         if el in TITLE]

    ##  5) DOMAIN tokenized intersection with RDAP
    domain_tokenized_intersection_rdap = check_intersection(
        domain_tokenized_s, used_rdap_fields_ls)

    ## 6) TITLE tokenized intersection with RDAP
    title_tokenized_intersect_rdap = check_intersection(
        title_tokenized_s, used_rdap_fields_ls)

    return (
        domain_in_rdap,  # 1
        rdap_in_domain,  # 2
        title_in_rdap,  # 3
        rdap_in_title,  # 4
        domain_tokenized_intersection_rdap,  # 5
        title_tokenized_intersect_rdap,  # 6
    )
