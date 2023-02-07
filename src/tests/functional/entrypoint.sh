#!/bin/sh

sh -c "./tests/functional/testdata/schema.sh \
    && pip3 install -r tests/functional/requirements.txt \
    && python3 -m pytest tests/functional/src"