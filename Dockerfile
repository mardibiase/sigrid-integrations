FROM python:slim-latest

COPY report-generator/ /sources

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3-lxml \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \ 
    && pip install /sources \
    && rm -rf /sources

COPY objectives-report /integrations/objectives-report

RUN pip install -r /integrations/objectives-report/requirements.txt

ENV PATH="/integrations/objectives-report:${PATH}"
