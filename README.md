fiche [![Build Status](https://travis-ci.org/solusipse/fiche.svg?branch=master)](https://travis-ci.org/solusipse/fiche)
=====

Command line pastebin for sharing terminal output.

# Client-side usage

Self-explanatory live examples (using public server):

```
echo just testing! | nc termbin.com 9999
```

```
cat file.txt | nc termbin.com 9999
```

In case you installed and started fiche on localhost:

```
ls -la | nc localhost 9999
```

You will get an url to your paste as a response, e.g.:

```
http://termbin.com/ydxh
```

You can use our beautification service to get any paste colored and numbered. Just ask for it using `l.termbin.com` subdomain, e.g.:

```
http://l.termbin.com/ydxh
```

### Browser-based usage

You can also create and view pastes entirely from a web browser using the bundled `extras/lines` web app (see [Web Interface](#web-interface) below).

-------------------------------------------------------------------------------

## Useful aliases

You can make your life easier by adding a termbin alias to your rc file. We list some of them here:

-------------------------------------------------------------------------------

### Pure-bash alternative to netcat

__Linux/macOS:__
```
alias tb="(exec 3<>/dev/tcp/termbin.com/9999; cat >&3; cat <&3; exec 3<&-)"
```

```
echo less typing now! | tb
```

_See [#42](https://github.com/solusipse/fiche/issues/42), [#43](https://github.com/solusipse/fiche/issues/43) for more info._

-------------------------------------------------------------------------------

### `tb` alias

__Linux (Bash):__
```
echo 'alias tb="nc termbin.com 9999"' >> .bashrc
```

```
echo less typing now! | tb
```

__macOS:__

```
echo 'alias tb="nc termbin.com 9999"' >> .bash_profile
```

```
echo less typing now! | tb
```

-------------------------------------------------------------------------------

### Copy output to clipboard

__Linux (Bash):__
```
echo 'alias tbc="netcat termbin.com 9999 | xclip -selection c"' >> .bashrc
```

```
echo less typing now! | tbc
```

__macOS:__

```
echo 'alias tbc="nc termbin.com 9999 | pbcopy"' >> .bash_profile
```

```
echo less typing now! | tbc
```

__Remember__ to reload the shell with `source ~/.bashrc` or `source ~/.bash_profile` after adding any of provided above!

-------------------------------------------------------------------------------

## Requirements
To use fiche you have to have netcat installed. You probably already have it - try typing `nc` or `netcat` into your terminal!

-------------------------------------------------------------------------------

# Server-side usage

## Installation

1. Clone:

    ```
    git clone https://github.com/solusipse/fiche.git
    ```

2. Build:

    ```
    make
    ```
    
3. Install:

    ```
    sudo make install
    ```

### Using Ports on FreeBSD

To install the port: `cd /usr/ports/net/fiche/ && make install clean`. To add the package: `pkg install fiche`.

_See [#86](https://github.com/solusipse/fiche/issues/86) for more info._

-------------------------------------------------------------------------------

## Usage

```
usage: fiche [-D6epbsdSolBuw].
             [-d domain] [-L listen_addr ] [-p port] [-s slug size]
             [-o output directory] [-B buffer size] [-u user name]
             [-l log file] [-b banlist] [-w whitelist] [-S]
```

These are command line arguments. You don't have to provide any of them to run the application. Default settings will be used in such case. See section below for more info.

### Settings

-------------------------------------------------------------------------------

#### Output directory `-o`

Relative or absolute path to the directory where you want to store user-posted pastes.

```
fiche -o ./code
```

```
fiche -o /home/www/code/
```

__Default value:__ `./code`

-------------------------------------------------------------------------------

#### Domain `-d`

This will be used as a prefix for an output received by the client.
Value will be prepended with `http`.

```
fiche -d domain.com
```

```
fiche -d subdomain.domain.com
```

```
fiche -d subdomain.domain.com/some_directory
```

__Default value:__ `localhost`

-------------------------------------------------------------------------------

#### Slug size `-s`

This will force slugs to be of required length:

```
fiche -s 6
```

__Output url with default value__: `http://localhost/xxxx`,
where x is a randomized character

__Output url with example value 6__: `http://localhost/xxxxxx`,
where x is a randomized character

__Default value:__ 4

-------------------------------------------------------------------------------

#### HTTPS `-S`

If set, fiche returns url with https prefix instead of http

```
fiche -S
```

__Output url with this parameter__: `https://localhost/xxxx`,
where x is a randomized character

-------------------------------------------------------------------------------

#### User name `-u`

Fiche will try to switch to the requested user on startup if any is provided.

```
fiche -u _fiche
```

__Default value:__ not set

__WARNING:__ This requires that fiche is started as a root.

-------------------------------------------------------------------------------

#### Buffer size `-B`

This parameter defines size of the buffer used for getting data from the user.
Maximum size (in bytes) of all input files is defined by this value.

```
fiche -B 2048
```

__Default value:__ 32768

-------------------------------------------------------------------------------

#### Log file `-l`

```
fiche -l /home/www/fiche-log.txt
```

__Default value:__ not set

__WARNING:__ this file has to be user-writable

-------------------------------------------------------------------------------

#### Ban list `-b`

Relative or absolute path to a file containing IP addresses of banned users.

```
fiche -b fiche-bans.txt
```

__Format of the file:__ this file should contain only addresses, one per line.

__Default value:__ not set

__WARNING:__ not implemented yet

-------------------------------------------------------------------------------

#### White list `-w`

If whitelist mode is enabled, only addresses from the list will be able
to upload files.

```
fiche -w fiche-whitelist.txt
```

__Format of the file:__ this file should contain only addresses, one per line.

__Default value:__ not set

__WARNING:__ not implemented yet

-------------------------------------------------------------------------------

### Running as a service

There's a simple systemd example:
```
[Unit]
Description=FICHE-SERVER

[Service]
ExecStart=/usr/local/bin/fiche -d yourdomain.com -o /path/to/output -l /path/to/log -u youruser

[Install]
WantedBy=multi-user.target
```

__WARNING:__ In service mode you have to set output directory with `-o` parameter.

-------------------------------------------------------------------------------

### Example nginx config

Fiche has no http server built-in, thus you need to setup one if you want to make files available through http.

There's a sample configuration for nginx:

```
server {
    listen 80;
    server_name mysite.com www.mysite.com;
    charset utf-8;

    location / {
            root /home/www/code/;
            index index.txt index.html;
    }
}
```

-------------------------------------------------------------------------------

## Web Interface

The `extras/lines` directory contains a Flask-based web application (`lines.py`) that turns fiche into a **fully browser-usable pastebin**.  It provides:

* **A paste-submission form** at `/` — type or paste text, click *Submit*, and receive a shareable URL.
* **Syntax-highlighted paste viewing** at `/<slug>` — any paste (whether submitted through the web form or via `nc`) is displayed with line numbers and automatic language detection, powered by [Pygments](https://pygments.org/).

### Requirements

```
pip install flask pygments
```

### Running

```
python extras/lines/lines.py /path/to/output/directory
```

Then open `http://localhost:5000` in your browser.

> **Note:** The paste *storage* directory must be the same directory used by the fiche TCP server (`-o` flag) if you want both interfaces to share pastes.

-------------------------------------------------------------------------------

## Docker

A `Dockerfile` and `docker-compose.yml` are provided so you can run fiche (and the optional web interface) in containers with data persisted across restarts.

### Quick start with Docker Compose

```bash
# Start both the fiche TCP server (port 9999) and the Lines web UI (port 5000)
docker compose up -d
```

> **Note:** `docker compose` (without a hyphen) requires Docker Engine 20.10+ with the Compose V2 plugin. On older installations use `docker-compose` (with a hyphen) instead.

Paste data is stored in the `fiche_data` named Docker volume and survives container restarts or re-creation.

### Customising the domain

Override the default command to pass your public domain name:

```yaml
# docker-compose.yml
services:
  fiche:
    command: ["-o", "/data", "-d", "yourdomain.com"]
```

Or with plain Docker:

```bash
docker build -t fiche .
docker run -d \
  -p 9999:9999 \
  -v fiche_data:/data \
  fiche -o /data -d yourdomain.com
```

### Bind-mount instead of a named volume

To store pastes directly on the host filesystem replace the volume reference in `docker-compose.yml`:

```yaml
volumes:
  - /host/path/to/pastes:/data
```

### Accessing pastes

After starting, send text with netcat:

```bash
cat file.txt | nc localhost 9999
```

Open the returned URL in a browser, or browse all pastes through the Lines web UI at `http://localhost:5000`.

-------------------------------------------------------------------------------

## License

Fiche is MIT licensed.
