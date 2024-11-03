# Setup & Usage

The following steps only concern the backend (also referred to as server). In case you need to build the frontend yourself, see [root README](../README.md#building--starting), or see the [frontend README](../frontend/README.md) for running a frontend development server.

## Prerequisites

- At least Python 3.10.x - [python.org](https://www.python.org/)
- pip - usually comes with python.

## Setup

- Execute `pip install -r requirements.txt` inside the backend folder. This will install all server requirements.
- Take a look at the config `backend/config.json` and change the `experimenter_password`. Details can be seen in the [configuration section](#configuration) bellow.

## Start

To start the server, execute `python3 main.py` inside the `backend` folder.

Depending on your python installation, `python3` may need to be replaced with `py` or `python`.

For testing, the `testing_main.py` provides an alternative to the above `main.py`. It starts the server the same way `main.py` does, but also creates and starts an experiment for the session `bbbef1d7d0`. This was used for quick testing with participants, to avoid the need to connect as experimenter before each test.

# Configuration

The backend can be configured using the `backend/config.json`.

- `experimenter_password` - str: password experimenters must provide to authenticate themselves
- `host` - str : host address the backend should use
- `port` - int : port the backend should use
- `environment` - str : `dev` or `prod`
- `serve_frontend` - bool : Whether the server should serve the frontend. Set to `false` if the frontend is hosted by a different server (see note bellow)
  - Developer Note: A better way to host the frontend would be using a [Reverse Proxy](https://en.wikipedia.org/wiki/Reverse_proxy) like [nginx](https://nginx.org/) or [CDN](https://en.wikipedia.org/wiki/Content_delivery_network) services, as noted in [aiohttp](https://docs.aiohttp.org/en/stable/web_advanced.html?highlight=static#static-file-handling) which we use for hosting.
- `https` - bool : Whether the backend should use https
- `ssl_cert` - str : path to ssl certificate. Only used if https is true
- `ssl_key` - str : path to ssl private key. Only used if https is true
- `log` - str : Logging level for Hub. Must be one of: `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. Default: `INFO`
- `log_file` - null | str : If given, the logger will write the log into the file instead of the console
- `log_dependencies` - str : Logging level for project 3rd party dependencies (see [requirements.txt](./requirements.txt)). Must be one of: `CRITICAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. Default: `WARNING`. Using `INFO` or `DEBUG` may lead to a strong increase in output.
- `ping_subprocesses` - int : If greater than 0, all subprocesses will be pinged in an interval defined by the value of `ping_subprocesses` (in seconds). Used for debugging, default should be `0`.
- `experimenter_multiprocessing` - bool : If true, experimenter connections will be executed on independent processes
- `participant_multiprocessing` - bool : If true, participant connections will be executed on independent processes

## Logging overview

The following logging levels are available for `log` and `log_dependencies` in the [configuration](#configuration):

| Logger output | `DEBUG` | `INFO` | `WARNING` | `ERROR` | `CRITICAL` |
| ------------- | :-----: | :----: | :-------: | :-----: | :--------: |
| debug         |    x    |   -    |     -     |    -    |     -      |
| info          |    x    |   x    |     -     |    -    |     -      |
| warning       |    x    |   x    |     x     |    -    |     -      |
| error         |    x    |   x    |     x     |    x    |     -      |
| critical      |    x    |   x    |     x     |    x    |     x      |

- If the logger is set to `INFO`, information with the debug level is ignored and only important events are logged, possibly with less detail.
- If the logger is set to `DEBUG` everything is logged. This also includes additional information that can be helpful in debugging.

# Using a SSL Certificate

Most browsers only allow access to media devices (webcam, microphone, ...) if the website is localhost or HTTPS. Additionally, websites served over HTTPS can not make requests to HTTP servers. Therefore a SSL certificate is required to access the backend from other devices.

Place the certificate and private key in `backend/certificate` and make sure `ssl_cert` and `ssl_key` in `config.json` are set correctly.
Then set `https` to `true` and start the server.

In case the frontend dev server is used, make sure to update the backend server address there. See [frontend readme](./../frontend/README.md#configuring-the-development-server).

## Acquiring a SSL Certificates

If you want to conduct an experiment, you need to get a trusted SSL Certificate. One way to get free SSL certificates is [Let's Encrypt](https://letsencrypt.org/).

## Using a Self Signed Certificate

For development and testing purposes, self signed certificates can be used. **Don't use self signed certificates for production!**

A bash script using openssl to generate a self signed certificate can be found at: `backend/certificate/generate_certificate.sh`. You can check if openssl is installed using: `openssl version`.

In case openssl is not an option, take a look at [Generating self-signed certificates on Windows](https://medium.com/the-new-control-plane/generating-self-signed-certificates-on-windows-7812a600c2d8).

When using a self signed certificate, your browser will likely warn you about it.
To allow the frontend to connect to the server, you must manually "accept the risk" by directly opening the backend in the browser. The server will tell you its address after starting, it will look something like: https://127.0.0.1:8080.

# Development Guidelines

See [Contributing](./../CONTRIBUTING.md).
