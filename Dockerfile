FROM python:latest

COPY report-generator/ /sources

RUN pip install /sources \
    && rm -rf /sources

COPY objectives-report /integrations/objectives-report

RUN pip install -r /integrations/objectives-report/requirements.txt

ENV PATH="/integrations/objectives-report:${PATH}"
