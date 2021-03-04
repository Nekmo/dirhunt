
.. image:: https://raw.githubusercontent.com/Nekmo/dirhunt/v0.2.0/images/dirhunt.png

|


.. image:: https://img.shields.io/github/workflow/status/Nekmo/dirhunt/Tests.svg?style=flat-square&maxAge=2592000
  :target: https://github.com/Nekmo/dirhunt/actions?query=workflow%3ATests
  :alt: Latest Tests CI build status

.. image:: https://img.shields.io/pypi/v/dirhunt.svg?style=flat-square
  :target: https://pypi.org/project/dirhunt/
  :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/pyversions/dirhunt.svg?style=flat-square
  :target: https://pypi.org/project/dirhunt/
  :alt: Python versions

.. image:: https://img.shields.io/codeclimate/maintainability/Nekmo/dirhunt.svg?style=flat-square
  :target: https://codeclimate.com/github/Nekmo/dirhunt
  :alt: Code Climate

.. image:: https://img.shields.io/codecov/c/github/Nekmo/dirhunt/master.svg?style=flat-square
  :target: https://codecov.io/github/Nekmo/dirhunt
  :alt: Test coverage

.. image:: https://img.shields.io/requires/github/Nekmo/dirhunt.svg?style=flat-square
     :target: https://requires.io/github/Nekmo/dirhunt/requirements/?branch=master
     :alt: Requirements Status


Dirhunt
#######

.. image:: https://asciinema.org/a/xPJXT0MhrvlZ8lJYJYkjxlice.png
     :target: https://asciinema.org/a/xPJXT0MhrvlZ8lJYJYkjxlice
     :align: center
     :alt: Dirhunt Demo Video


Dirhunt is a web crawler optimize for **search and analyze directories**. This tool can find interesting things if the
server has the *"index of"* mode enabled. Dirhunt is also useful if the directory listing is not enabled. It detects
directories with **false 404 errors**, directories where an **empty index file** has been created to hide things and
much more.

.. code-block:: console

    $ dirhunt http://website.com/

Dirhunt does not use brute force. But neither is it just a **crawler**. This tool is faster than others because it
minimizes requests to the server. Generally, this tool takes **between 5-30 seconds**, depending on the website and
the server.

Read more about **how to use** Dirhunt `in the documentation <http://docs.nekmo.org/dirhunt/usage.html>`_.


Features
========

* Process **one or multiple sites** at a time.
* Process *'Index Of'* pages and report interesting files.
* Detect **redirectors**.
* Detect **blank index file** created on directory to hide things.
* Process some html files in search of new directories.
* 404 error pages and detect **fake 404 errors**.
* Filter results by **flags**.
* Analyze results at end. It also **processes date & size** of the Index Pages.
* Get new directories using **robots.txt**, **VirusTotal** & **Google**.
* **Delay** between requests.
* One or multiple **proxies** option. It can also search for **free proxies**.
* **Save the results** to a JSON file (NEW!)
* **Resume** the aborted scans (NEW!)


Install
=======
If you have Pip installed on your system, you can use it to install the latest Dirhunt stable version::

    $ sudo pip3 install dirhunt

Python 2.7 & 3.5-3.8 are supported but Python 3.x is recommended. Use ``pip2`` on install for Python2.

There are other `installation methods <http://docs.nekmo.org/dirhunt/installation.html>`_ available.


Disclaimer
==========
This software must not be used on third-party servers without permission. Dirhunt has been created to be used by audit
teams with the consent of the owners of the website analyzed. The author is not responsible for the use of this tool
outside the law.

This software is under the MIT license. The author does not provide any warranty. But issues and pull requests are
welcome.
