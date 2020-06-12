FROM continuumio/miniconda3:4.7.12
RUN apt-get update --fix-missing && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*
RUN conda install -y -c conda-forge \
  bokeh=2.0.2 \
  nbconvert=5.6.1 \
  jupyter_client \
  nb_conda \
  pymongo \
  pandas \
  holoviews
ADD crontab /etc/cron.d/report-job
ADD ssutils.py /opt/ssutils.py
ADD analysis.ipynb /opt/analysis.ipynb
ADD build-report-docker /opt/build-report
RUN chmod +x /opt/build-report
RUN chmod 0644 /etc/cron.d/report-job
RUN touch /var/log/cron.log
WORKDIR /opt
CMD /opt/build-report && cron && tail -f /var/log/cron.log