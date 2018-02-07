
.. image:: https://raw.githubusercontent.com/Nekmo/dirhunt/v0.2.0/images/dirhunt.png

Dirhunt
#######
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


Install
=======
If you have Pip installed on your system, you can use it to install Dirhunt::

    $ sudo pip3 install dirhunt

At this time only **Python 3.4+** is officially supported. Other versions may work without guarantees.

There are other `installation methods <http://docs.nekmo.org/dirhunt/installation.html>`_ available.


Disclaimer
==========
This software must not be used on third-party servers without permission. Dirhunt has been created to be used by audit
teams with the consent of the owners of the website analyzed. The author is not responsible for the use of this tool
outside the law.

This software is under the MIT license. The author does not provide any warranty. But issues and pull requests are
welcome.
