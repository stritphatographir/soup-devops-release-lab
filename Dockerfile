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

FROM ${PYTHON_IMAGE} AS artifact-verified
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /project
COPY requirements/runtime.lock requirements/build.lock ./requirements/
COPY scripts/bundle.py scripts/smoke_artifact.py ./scripts/
COPY ci-artifact/ /release/
ARG SOURCE_SHA
RUN test -n "$SOURCE_SHA" && python scripts/bundle.py /release --source-sha "$SOURCE_SHA"
RUN python scripts/smoke_artifact.py --bundle /release --kind wheel
RUN python scripts/smoke_artifact.py --bundle /release --kind sdist

FROM ${PYTHON_IMAGE} AS runtime-base
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1
COPY requirements/runtime.lock /runtime.lock
RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip --isolated install --index-url https://pypi.org/simple --only-binary=:all: --require-hashes -r /runtime.lock
WORKDIR /tmp
ENTRYPOINT ["/opt/venv/bin/soup-check"]

FROM runtime-base AS artifact-runtime
COPY --from=artifact-verified /release/dist/ /release/
RUN /opt/venv/bin/python -m pip --isolated install --no-deps --no-index /release/*.whl && \
    /opt/venv/bin/python -m pip check && rm -rf /release
USER 10001:10001

# Standalone source builds retain an explicit local recipe path. Actions uses
# artifact-runtime above, which consumes the same bundle as its native matrix.
FROM runtime-base AS runtime
COPY --from=verified /release/dist/ /release/
RUN /opt/venv/bin/python -m pip --isolated install --no-deps --no-index /release/*.whl && \
    /opt/venv/bin/python -m pip check && rm -rf /release
USER 10001:10001
