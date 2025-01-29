FROM python:alpine

COPY report-generator/ /sources/report-generator
COPY objectives-report /integrations/objectives-report
COPY get-scope-file/ /integrations/get-scope-file

RUN apk add --no-cache \
        py3-lxml=5.3.0-r0 \
    && adduser -S sigrid \
    && pip install --no-cache-dir /sources/report-generator \
    && rm -rf /sources \
    && pip install --no-cache-dir -r /integrations/objectives-report/requirements.txt

ENV PATH="/integrations/objectives-report:/integrations/get-scope-file:${PATH}"
USER sigrid
WORKDIR /home/sigrid