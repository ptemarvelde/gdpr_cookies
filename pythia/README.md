# README

## Pythia
[Pythia] is a framework for identifying Web content hosted on
third-party infrastructures, including both traditional Web hosts and
content delivery networks.

The design and evaluation of Pythia is detailed in our 
[WWW 2019 paper](https://doi.org/10.1145/3308558.3313664):
> Srdjan Matic, Gareth Tyson and Gianluca Stringhini.
Pythia: a Framework for the Automated Analysis of Web Hosting Environments
In Proceedings of the 2019 World Wide Web Conference
(WWW '19), May 13-17, 2019, San Francisco, CA, USA

In a nutshell, Pythia comprises two phases: (I) the download of a
webpage using Selenium and (II) a check if the webpage was obtained
from a third-party hosting service. Code for both is included, but the
two phases can be performed separately. In addition to this, the tool
is developed in a modular way which makes possible to reproduce any
minor task that is relevant for each phase (e.g., the resolution of a
domain name before obtaining a resource from a URL, the collection of
RDAP information for a particular IP address).

### Installation - tested on Debian GNU/Linux 9.7 (strech) with 4.9.0.8-amd64 kernel
To run our framework, the following components are required:
1. **python** (in addition with a bunch of external libraries)
2. **google-chrome**
3. **chromedriver**,  which is used for controlling google-chrome

Python and the external libraries can be installed through the command line:
```
$ sudo apt-get install python3-pip
$ pip3 install --upgrade ipwhois tldextract wordsegment selenium bs4 dnspython intervaltree netaddr nltk psutil
```

The following commands will download ad install the debian package containing google-chrome:
```
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
sudo apt --fix-broken install
```

Make sure to download a **chromedriver** compatible with the *Google Chrome* version that you have installed on your sytem. The **chromedriver** and additional information can be obtained from the following [link](http://chromedriver.chromium.org/downloads).


### Dependencies
1. *Script:* **dns\_resolve.py**
*Repo dependencies:* -
*External dependencies:* dnspython

2. *Script:* **rdap\_query.py**
*Repo dependencies:* -
*External dependencies:* ipwhois intervaltree netaddr

3. *Script:* **selenium\_driver\_chrome.py**
*Repo dependencies:* -
*External dependencies:* selenium

4. *Script:* **process\_struct.py**
*Repo dependencies:* -
*External dependencies:* -

5. *Script:* **extract\_processed\_uris.py**
*Repo dependencies:* -
*External dependencies:* -

6. *Script:* **task\_manager.py**
*Repo dependencies:* dns\_resolve.py, rdap\_query.py, selenium\_driver\_chrome.py, extract\_processed\_uris.py, process\_struct.py
*External dependencies:* intervaltree netaddr psutil

7. *Script:* **check\_ownership.py**
*Repo dependencies:* -
*External dependencies:* tldextract nltk wordsegment

8. *Script:* **hosting\_detector.py**
*Repo dependencies:* task\_manager.py check\_ownership.py
*External dependencies:* -


### Scripts Purpose and Usage
1. *Script:* **dns\_resolve.py**
*Use:* performs the DNS resolution of a domain.
*Input:* a domain name in form of a string.
*Output:* DNS resolutions of the domain name received in input.
*Examples of use:* check ``__main__`` in **dns\_resolve.py**.

2. *Script:* **rdap\_query.py**
*Use:* use the RDAP protocol to obtain inforamtion about the ownership of an IP address.
*Input:* a string representing an IP address or a CIDR.
*Output:* RDAP ownership information about the IP/CIDR in the JSON format.
*Examples of use:* check ``__main__``in **rdap\_query.py**.

3. *Script:* **selenium\_driver\_chrome.py**
*Use:* fetches an HTML resource using Selenium and Google Chrome.
*Input:* a string that represents a URL.
*Output:* the HTML code with additional information about all the resources that were feched while loading the HTML content.
*Examples of use:* check ``__main__``in **selenium\_driver\_chrome.py**.

4. *Script:* **process\_struct.py**
*Use:* pack/unpack the information obtained using **selenium\_driver\_chrome.py**, **dns\_resolve.py** and **rdap\_query.py** into/from a JSON data structure.

5. *Script:* **extract\_processed\_uris.py**
*Use:* use the information stored in the JSON to generate a dictionary of the URLs that were processed with **selenium\_driver\_chrome.py**, **dns\_resolve.py** and **rdap\_query.py**
*Examples of use:* check ``__main__``in **extract\_processed\_uris.py**.

6. *Script:* **task-manager.py**
*Use:* download the HTML from a URL and obtain information about the domains and IP addresses that are contacted while loading the HTML content.
*Input:* a domain name or a list of domains.
*Output:* a JSON file that contains HTML pages obtained from the domains in input, the mapping domain->IP address and the RDAP information of the IP addresses from which the resources were downloaded.
*Examples of use:* check ``__main__``in **task\_manager.py**.
*Notes:* the parameters passed in input to the script are available in form of global variables which are included at the beginning of **task\_manager.py**. These parameters allow to configure: 
 - the maximum timeout after which the page will be considered completely loaded (``GL_browser_PAGE_LOAD_TIMEOUT``)
 - the service that is used to find the public IP address on which the crawler is running (``GL_SOURCE_IP``)
 - the path to the output file where all the collected information is stored in the JSON format (``GL_OUTPUT_FILE``)
 - the path to the log file where errors and exceptions are logged (``GL_EXCEPTION_LOG_FILE``)
 - the number of parallel instances of crawler that will be run (``GL_MAX_NUM_CHROMEDRIVER_INSTANCES``)
 - the number of URLs that will be processed in a single chunk (``GL_CRAWL_CHUNK_SIZE``)
 - the waiting time that the crawler will sleep before collecting information for another chunk (``GL_CRAWL_CHUNK_SLEEP``)
 - the list of domains/URLs that will be visited (``GL_URI_FILE``)
 - the maximum number of domains/URLs that will be visited (``GL_MAX_DOMAINS_TO_CONTACT``)
 - if to shuffle or not the list of domains/URLs that the framework receives in input (``GL_SHUFFLE_DOMAINS_LIST``)

7. *Script:* **check\_ownership.py**
*Use:* compare information obtained from the HTML and the domain name with the ownership of the IP address from which the resource was downloaded, to check if the owner of the webpage is the same as the owner of the IP range.
*Input:* the title of the HTML webpage, the domain name and the RDAP information about the IP address.
*Output:* the result of various checks that search for evidence that the owner of the HTML or the domain is the same as the owner of the IP address range.

8. *Script:* **hosting\_detector.py**
*Use:* inspect the information collected with **task\_manager.py** and identify the webpages that are self-hosted (i.e., where the HTML was not downloaded from a IP that belongs to a third-party).
*Input:* the JSON created after executing **task\_manager.py**.
*Output:* a CSV file containing the URL initially loaded in the browser (*starting\_URL*), the URL on which the browser ended after trying to load the resource (*landing\_URL*) and the fact that the owner of the *landing\_URL* is also the same as the owner of the IP address from which the resource was downloaded.
*Notes:* the parameters passed in input to the script are available in form of global variables which are included at the beginning of **hosting\_detector.py**. These parameters allow to configure: 
 - if to print or not information on the standard output (``PRINT_ON_STDOUT``)
 - the source file containing the JSON information (``GL_PREPROCESSED_JSON_DATA``)
 - the output file where the hosting information will be stored in the CSV format (``GL_OUTPUT_CVS_FILE``)

#### OK, but how I cant just simply run it?
The tool has been developed with the idea of determining of a *domain is self-hosted or it uses third-party services* (e.g., the owner of the HTML that can be downloaded from the domain is the same as the owner the owner of the IP address from which the resource was downloaded).
To this end the framework:
1. receives in input list of domains;
2. for each domain it expands the domain name with the "http://", "https://", "http://www.", "https://www." prefixes;
3. for each of the four URLs generated in the previous step, Pythia downloads the HTML from the home page. During the process the framework collects also information about the resolution of the domains that appear in the resources embedded in the HTML and uses RDAP to obtain ownership information about IP addresses. All the collected information is stored in a file with using the JSON format;
4. finally, Pythia uses the information obtained in step #3, to check if the owner of the webpage corresponds to the owner of the IP address from which the resource was downloaded.

After cloning the repository, you will notice that there is a ``samples`` directory. The file ``samples/uris.csv`` contains the list of domain names for which Pythia will collect the ownership information. You can edit this file to include new domains that you want to inspect with Pythia.

Once you finished editing the file, you instruct to collect information about those domains. To achieve this, open a terminal and type:
``python3 task_manager.py``
All the information gathered by Pythia will be available in the **samples/example.json** file.

Once Pythia has gathered all the information about the URLs, you can check which of those URLs are *self-hosted*. To achieve this, open a terminal and type:
``python3 hosting_detector.py``
In addition to standard output, information about which URLs are self-hosted will be available in the **samples/example_hosting.csv** file.

NOTE: each domain (*example.org*) is expanded into four different URLs (*http://example.org/*, *https://example.org/*, *http://www.example.org/*, *https://www.example.org/*). Those four starting URLs could lead *up to four different* landing pages which might host different contents that are fetched from various IP address. For each one of such pages, we check if the owner of the page is the same of the owner of the IP address range.
