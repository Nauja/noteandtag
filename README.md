# NoteAndTag

[![Build Status](https://travis-ci.com/Nauja/noteandtag.png?branch=master)](https://travis-ci.com/Nauja/noteandtag)
[![Documentation Status](https://readthedocs.org/projects/noteandtag/badge/?version=latest)](https://noteandtag.readthedocs.io/en/latest/?badge=latest)
[![Test Coverage](https://codeclimate.com/github/Nauja/noteandtag/badges/coverage.svg)](https://codeclimate.com/github/Nauja/noteandtag/coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/Nauja/noteandtag/issues)

Website and REST API for taking notes and organizing by tags

## Online demo

You can test the website online at [noteandtag.jeremymorosi.com](http://noteandtag.jeremymorosi.com):

![alt text](http://cdn.jeremymorosi.com/noteandtag/website_preview.png "Preview")

You can test the REST API online at [noteandtag.jeremymorosi.com/api/v1/doc](http://noteandtag.jeremymorosi.com/api/v1/doc):

![alt text](http://cdn.jeremymorosi.com/noteandtag/swagger_preview.png "Preview")

The documentation is generated by `aiohttp_swagger`.

## Usage

You can run the service as:

```bash
python -m noteandtag {config_directory}
```

You can show help with `noteandtag --help`:

```
usage: noteandtag [-h] [-v] directory

Website and REST API for taking notes and organizing by tags

positional arguments:
  directory      config directory

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Verbosity level

```

To quick start using *NoteAndTag*, you can download this repository and run:

```bash
python -m noteandtag etc
```

The default [`etc/config.cnf`](https://github.com/Nauja/noteandtag/blob/master/etc/config.cnf) configuration file looks like this:

```
[service]
port = 8080
base-url = /
api-base-url = /api/v1/
cdn-url = /static
static-dir = static
jinja2-templates-dir = etc/templates
default-theme = monokaiorange
swagger-yml = etc/swagger.yml
swagger-url = /api/v1/doc
db = etc/db.yml
```

Where:

  * **port**: is the public port to access the service.
  * **base-url**: is the base URL to access the index page.
  * **api-base-url**: is the base URL to access the REST API.
  * **cdn-url**: is an optional URL to serve static JS and CSS files.
  * **static-dir**: is the path to local static JS and CSS files.
  * **default-theme**: is the default theme users will see.
  * **jinja2-templates-dir**: is the path to local Jinja2 templates files.
  * **swagger-yml**: is the path to local Swagger description file.
  * **swagger-url**: is the base URL to access Swagger documentation.
  * **db**: is the file where notes will be saved.

You should now see:

```bash
======== Running on http://0.0.0.0:8080 ========
(Press CTRL+C to quit)

```

Meaning you can go to `http://localhost:8080` and start using *NoteAndTag*.

## Running with Docker

You can build a Docker image by downloading this repository and running:

```bash
docker build -t noteandtag:latest .
```

Next, run the Docker image as:

```bash
docker run \
 -v /path/to/etc:/etc/service \
 -v /path/to/log:/var/log/service \
 -p 8080:8080 \
 -it noteandtag:latest
```

Where:
  * **/path/to/etc**: is the path to the directory containing **config.cnf**.
  * **/path/to/log**: is the path to the directory where you wan't to store logs.
  * **8080**: is the public port to access the service.

As the Docker image exposes `/etc/service`, your typical `config.cnf` configuration file would be:

```
[service]
port = 8080
base-url = /
api-base-url = /api/v1/
cdn-url = /static
static-dir = /etc/service/static
jinja2-templates-dir = /etc/service/templates
default-theme = monokaiorange
swagger-yml = /etc/service/swagger.yml
swagger-url = /api/v1/doc
db = /etc/service/db.yml
```

You should now see:

```bash
======== Running on http://0.0.0.0:8080 ========
(Press CTRL+C to quit)

```

Meaning the service is up and ready.

## Testing

The `test` directory contains many tests that you can run with:

```python
python setup.py test
```

Or with coverage:

```python
coverage run --source=noteandtag setup.py test
```
