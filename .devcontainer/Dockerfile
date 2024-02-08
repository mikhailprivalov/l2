FROM python:3

ENV PYTHONUNBUFFERED 1

WORKDIR /workspace

COPY poetry.lock pyproject.toml /workspace/

RUN pip3 install poetry

RUN make install
