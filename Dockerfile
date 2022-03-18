FROM joyzoursky/python-chromedriver:latest

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
ENV LOCAL_RUN=False


WORKDIR /usr/workspace/pythia

CMD ["python3", "selenium_driver_chrome.py"]
# CMD ["python3", "task_manager.py"]

# TO run for development: # in root dir of project
# docker build . -t selenium:latest
# --shm-size is needed for high resource pages
# docker run -v ${PWD}:/usr/workspace -it --shm-size=2048m selenium:latest
# also add --entrypoint=/bin/sh to launch it as shell so you can run/test other stuff.
