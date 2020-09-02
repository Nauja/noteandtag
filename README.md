# NoteAndTag

[![Build Status](https://travis-ci.org/Nauja/noteandtag.png?branch=master)](https://travis-ci.com/Nauja/noteandtag)
[![Documentation Status](https://readthedocs.org/projects/noteandtag/badge/?version=latest)](https://noteandtag.readthedocs.io/en/latest/?badge=latest)
[![Test Coverage](https://codeclimate.com/github/Nauja/noteandtag/badges/coverage.svg)](https://codeclimate.com/github/Nauja/noteandtag/coverage)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/Nauja/noteandtag/issues)

Website and REST API for taking notes and organizing by tags

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
  * **/path/to/etc**: is the path to the service directory containing **config.cnf**.
  * **/path/to/log**: is the path to the directory where you wan't to store logs.
  * **8080**: is the public port to access the REST API.

You should see:

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
