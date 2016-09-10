# VA-Master
This is the core project of VapourApps, the master which contains:
* The dashboard
* The REST API
* The scheduler (spawning instances using `salt-cloud`, life-checks, key-value db)

## Installing
Requirements for installing:
* Debian Server 8 or any derivative (such as Ubuntu Server)
* No servers running on tcp/80, tcp/443, tcp/8600, tcp/8500, tcp/8400, tcp/8300
* Python 2.7 and pip

```bash
sudo pip install .
sudo vapourapps start 10.0.10.12 # enter the ip from which this machine can be accessed
```

### Development mode
Additional requirements for development:
* NodeJS (to compile dashboard JavaScript code)
* npm (to compile dashboard JavaScript code)

```bash
sudo pip install -e . # the additional flag allows editing Python code
sudo vapourapps start --dev 10.0.10.12
```

### virtualenv warning
`sudo pip` is not functional during a virtualenv session, because it's going to use
the system's pip executable. Instead, login as root before activating the session (`sudo -i`).
After doing that, everything should work nicely.

## Docs

The docs are available [here](docs/)

## Testing
At the moment we are working on a test suite, which should contain unit tests and integration tests (with Salt-Cloud and Consul).

## License
This project is distributed under [the GPL v3 license](http://www.gnu.org/licenses/gpl-3.0.en.html).
