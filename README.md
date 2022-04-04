## Launch/create VM:
    Compute Enginge -> VM instances -> Create an instance -> Set name to location it will run in -> Set region ->
    e2-medium (default) -> Boot disk image: select Ubuntu 20.04 -> Create
 
 Wait till VM is started then connect with ssh
 

install curl/git/needed packages for docker

    sudo apt-get update && sudo apt-get install git ca-certificates curl gnupg lsb-release 

download docker quick setup

    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

Clone repo (still have to give username/access token)

    git clone https://github.com/ptemarvelde/gdpr_cookies.git

Give credentials (password doesn't work, need to create access token)
Store git credentials

    git config --global credential.helper store

    git checkout dev (depends on branch ofc)

Build image

    cd gdpr_cookies/pythia
    sudo docker build -t hacking-lab-crawler:latest .
    cd ../

Run image (may need `sudo` for docker, so add it before the run command or do `sudo su`)

    docker run -v ${PWD}:/usr/workspace --env VM_LOCATION=$(< /etc/hostname) --env DUTCH_DOMAINS=True -it --shm-size=2048m hacking-lab-crawler:latest
    
## Pythia Extensions  
Pythia is extended in this project with the goal of achieving the right output of the results and a proper way of handling requests and responses using a local selenium chrome driver. The extended version of Pythia supports information gathering about the location of the server corresponding to a requested website. It also has the functionality for storing information about the page source and different kinds of cookies of a website into a json file. Furthermore, screenshot mechanism is also supported which makes it possible to store a screenshot of a website in an automatic fashion. 

In file `banner_config.py` the patterns for regex matching are contained along with the translation function. `get_banner_patterns` function translates the keywords that need to be translated using the Google Translate library. The function also gathers all the required patterns in one list and returns them.    
Furthermore, the files `selenium_driver_chrome.py` and `task_manager.py` have also been adapted to achieve our goal of getting the necessary information of all websites that are passed via the input.    

In `selenium_driver_chrome.py`, the function `download_with_browser` has been modified to also take in the screenshot directory and the banner patterns. A timeout before fetching the page source and after executing the request has been added so that the chance is higher than a banner is shown if there is one on the page. This aids in the identification process of whether a banner is shown or not. Moreover, a mechanism is added that takes a screenshot of the landing page of a website after the imposed timeout for manual checking and debugging. The fetched page source is analyzed in the `detect_banner` function which returns a dictionary of the matched patterns.    

In `task_manager.py`, the code where each chunk that needs to be crawled is changed to also pass the constant values of the patterns to the `fetch_info` (indirectly to `download_with_browser`). This is done so that the patterns are not reloaded each time in each forked process. The output directory is defined in the main function of the file. In addition, the file handling is also changed since the way that it was done by Pythia is a bit outdated as they used the `io` module for opening or creating a file for reading and writing. Now each time a file needs to be written to, it is opened and closed using the context manager of `open` function. The generated struct that is returned by `fetch_info` function is also modified to also include information gathered about cookies, banner detection and screenshot folder.
