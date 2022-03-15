FROM joyzoursky/python-chromedriver:latest

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

# TO run for development: # in root dir of project
# docker build . -t selenium:latest
# docker run -w /usr/workspace -v ${PWD}:/usr/workspace -it selenium:latest  /bin/sh