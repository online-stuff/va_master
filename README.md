# VA_Master
This is the core project of VapourApps, the master which contains:
* Consul (monitoring the apps and KV store)
* Salt Master (provisioning)
* The scheduler (containing API and dashboard)

## Installing
Requirements for installing:
* Debian Server 8 or any derivative (such as Ubuntu Server)
* No servers running on tcp/80, tcp/443, tcp/8600, tcp/8500, tcp/8400, tcp/8300
* Python 2.7 and pip

**Debian dependencies:** There are some OS-level dependencies that you can install
using the following command:

```bash
sudo sh -c "apt-get install -y build-essential python-dev libssl-dev libffi-dev libzmq3 libzmq-dev unzip supervisor && curl https://releases.hashicorp.com/consul/0.7.0/consul_0.7.0_linux_amd64.zip > consul.zip && unzip -d /usr/lib -o consul.zip consul"
```

**The software itself:** Install the software.

```bash
pip install vapourapps
vapourapps init
```

### Development on local machine
Additional requirements for development:
* NodeJS (to compile dashboard JavaScript code)
* npm (to compile dashboard JavaScript code)

```bash
pip install -e .
vapourapps init
# If you want to debug Python, detach it from supervisor and manually run code
sudo supervisorctl stop va_master
sudo virtualenv/bin/python -m va_master
```

## Docs

The docs are available [here](docs/)

## Testing
At the moment we are working on a test suite, which should contain unit tests and integration tests (with Salt-Cloud and Consul).

## License
This project is distributed under [the GPL v3 license](http://www.gnu.org/licenses/gpl-3.0.en.html).
