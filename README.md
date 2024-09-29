# MyEasyServer

*MyEasyServer helps you to deploy your home web server on a Raspberry Pi or a VPS as easily as possible*

<center><img width="160" src="docs/logo.svg" /></center>

## Introduction

This is the beginning of a new story: a new platform which will be deployed on a Raspberry Pi or a VPS web applications for your personal use. The goal is to keep the platform as simple as possible for the user.

You have to install a standard linux system (debian or ubuntu) and lauch the `install.sh` script.

It will deploy automatically everything for you.
You will have to point your browser to http://localhost:8080/ in order to access the web application and continue the configuration.

**WARNING** : This is software is not ready yet and just a work in progress.

Technically, this program is made of several components:
* a front end and a backend which are the UI and the server respectively for the web application. they are lauched in a docker container.
* a database which is a sqlite database (postres planned)
* a worker service which receives orders through a REST API and executes them.
* a Command Line Interface (CLI) which allows you to interact with the web application and the worker.

## Features 🌈

Features implemented yet:

* installer script

It **WILL** implement:

* Account management and token for API Authentication
* Mail server installation
* Spam services management
* Mail account configuration
* Web server management
* DNS zone management
* Log files management
* Firewall and security management

