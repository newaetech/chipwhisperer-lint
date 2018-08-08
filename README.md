# Overview #

This project is designed to help users perform automated testing of embedded hardware. This requires users to have certain hardware (ChipWhisperer) which is used to record example power traces.

With these traces we can perform analysis to determine how vulnerable a target device (normally - an AES crypto hardware core) is to side channel power analysis.

## Examples ##

For more details on this tool and results see the [White Paper](doc/CW_Lint_White_Paper.pdf). This was presented at Black Hat 2018.


See the following for examples and results:

 - doc folder with some small projects and output examples.
 - The [MBED-TLS Summary Build Demo](https://github.com/newaetech/cwlint-demo-aes-arm) .
 - The [Overlord-Talk Repo](https://github.com/newaetech/overlord-talk)

# Usage #

Let's get this thing working.

## Setup ##

Setting up requires running the backend server "somewhere". Basically it's supposed to run on EC2 server because they are a cheap way to get a bunch of cores and memory. You can do this locally as well, but it's fairly computationally intensive.

While there will be a hosted version, right now that is not available with a general interface. Thus it's easier if you run your own EC2 server.

## Using ##

The user has a number of power analysis traces, they were captured with a random plaintext and random fixed key. This random-random capture is done to reduce the chance one specific key is accidentally "picked off".

Briefly, it works like this:

1. Zips together a bunch of power traces.
2. Uploads files to server - by default the server.ini assumes they are in /var/cwlint/traces, so put them there and unzip.

Now call the server setup. Right now that looks like this:

```
python client.py run --cwproject="xmega-aes-small.cwp" --config="aes128_sbox.cfg"
```

This returns and tells you the project ID. The system then runs the check. You can then check for status of the request:

```
python client.py status 8
```

Finally making a HTML report.

```
python client.py result --html example_result.html 8
```

The report generation is currently a simple script -- this will be fixed eventually, but for the PoC has worked well enough (oops). It will likely happen on the backend since it will become much faster to download.
