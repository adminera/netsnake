# netsnake

<h1 align="center">
  <img src="static/netsnake.png" alt="netsnake" width="300px">
  <br>
</h1>

<h4 align="center">NetCat rewritten in Python</h4>

<p align="center">
  <a href="#Features">Features</a> •
  <a href="#Install">Install</a> •
  <a href="#Usage">Usage</a> 
  
</p>

---

Pesky system admins removed netcat from the server? Look no further, netsnake is your tool. netcat may be removed but python most likely isnt. Use this netcat replica made in python to own the server!

A powerful Python-based replacement for the traditional netcat tool. Designed to provide similar functionality for remote command execution, file transfer, and interactive shells—perfect for post-exploitation, debugging, or just a lightweight socket utility.

Built with offensive and defensive use cases in mind, especially on systems where Netcat is unavailable but Python is present.

# Features

- Remote command execution
- Interactive shell access
- File upload
- Client and server modes
- Clean CLI interface using argparse

# Install

```sh
git clone https://github.com/adminera/netsnake.git
cd netsnake
```

# Usage

```sh
python netsnake.py --help 
python3 netsnake.py --help
```

