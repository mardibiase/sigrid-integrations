FROM python:alpine

COPY report-generator/ /sources

RUN apk add --no-cache \
        py3-lxml=5.3.0-r0 \
    && pip install /sources \
    && rm -rf /sources

COPY objectives-report /integrations/objectives-report

RUN pip install -r /integrations/objectives-report/requirements.txt

ENV PATH="/integrations/objectives-report:${PATH}"
