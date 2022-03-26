FROM joyzoursky/python-chromedriver:latest

COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
ENV LOCAL_RUN=False
ENV DRIVER_LOG_LEVEL=INFO

WORKDIR /usr/workspace/pythia

# CMD ["python3", "selenium_driver_chrome.py"]
CMD ["python3", "task_manager.py", "combined_final_domains.csv"]

# TO run for development: # in root dir of project
# docker build . -t selenium:latest
# --shm-size is needed for high resource pages
# docker run -v ${PWD}:/usr/workspace -it --shm-size=2048m --env VM_LOCATION=$(< /etc/hostname) selenium:latest
# also add --entrypoint=/bin/sh to launch it as shell so you can run/test other stuff.
# --env DRIVER_LOG_LEVEL=INFO to set log level of some driver log statements