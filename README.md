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
Pythia is extended in this projct with the goal of achieving the right output of the results and a proper way of handling requests and responses using local selenium  chrome driver.  
In file `banner_config,py` the patterns for regex matching is contained along with translation function. `get_banner_patterns` function translates the keywords that need to be translated using Google Translate library. The function also gathers all the required patterns in one list and returns it. 
