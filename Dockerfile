# Versions
ARG PYTHON=python:3.12-alpine


## Stage one ##
FROM $PYTHON AS build
WORKDIR /usr/app
ARG BUILD_VERSION


# Install uv (cached as a separate layer)
RUN pip install --no-cache-dir uv


# Create a venv using uv (without gcc and virtualenv)
ENV VIRTUAL_ENV="/usr/app/venv"
RUN uv venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


# Copy and install dependencies (cacheable layer)
COPY requirements.txt .
RUN uv pip install --no-cache -r requirements.txt


## Stage two ##
FROM $PYTHON AS runtime
ARG BUILD_VERSION


# Create user and directories
RUN adduser -D cobra \
 && mkdir /usr/app \
 && chown cobra:cobra /usr/app
WORKDIR /usr/app


# Copy only the venv (without source code yet)
COPY --chown=cobra:cobra --from=build /usr/app/venv ./venv


# Copy only the required code (after venv for better caching)
COPY --chown=cobra:cobra . .


# Settings
USER cobra
ENV VIRTUAL_ENV="/usr/app/venv"
ENV PATH="/usr/app/venv/bin:$PATH"
EXPOSE 80


# Environment variables
ENV BUILD_VERSION=${BUILD_VERSION:-noversion}
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Metadata
LABEL app.version="${BUILD_VERSION}"


# Startup
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
CMD ["--port", "80", "--proxy-headers"]