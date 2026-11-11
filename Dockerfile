# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
FROM ${PYTHON_IMAGE} AS ci
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /project
COPY requirements/ requirements/
RUN python -m pip --isolated install --index-url https://pypi.org/simple --only-binary=:all: --require-hashes -r requirements/ci.lock

FROM ci AS build
COPY . .
RUN ruff check . && python -m pytest --cov --cov-branch
RUN python scripts/build_release.py --out /release

FROM ci AS verified
COPY --from=build /project/scripts/ /project/scripts/
COPY --from=build /release/ /release/
RUN python scripts/smoke_artifact.py --bundle /release --kind wheel
RUN python scripts/smoke_artifact.py --bundle /release --kind sdist

FROM ${PYTHON_IMAGE} AS runtime
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
COPY --from=verified /release/dist/ /release/
COPY requirements/runtime.lock /release/runtime.lock
RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip --isolated install --index-url https://pypi.org/simple --only-binary=:all: --require-hashes -r /release/runtime.lock && \
    /opt/venv/bin/python -m pip --isolated install --no-deps --no-index /release/*.whl && \
    /opt/venv/bin/python -m pip check && \
    rm -rf /release
USER 10001:10001
WORKDIR /tmp
ENTRYPOINT ["/opt/venv/bin/soup-check"]
