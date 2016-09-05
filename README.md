# VA-Master
This is the core project of VapourApps, the master which contains:
* The dashboard
* The REST API
* The scheduler (spawning instances using `salt-cloud`, life-checks, key-value db)

## Installing
The requirement for running it is a virtual machine with Debian 8 Server or any derivative such as Ubuntu Server. Python 2.7 must be installed. To install the master, run

```bash
git clone this_repo
mv this_repo /usr/lib/va_master/
./usr/lib/va_master/install.py dc1
```

## Docs

The docs are available [here](docs/)

## Testing
At the moment we are working on a test suite, which should contain unit tests and integration tests (with Salt-Cloud and Consul).

## License
This project is distributed under [the GPL v3 license](http://www.gnu.org/licenses/gpl-3.0.en.html). 
