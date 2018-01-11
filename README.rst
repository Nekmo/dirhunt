
Dirhunt
#######
Dirhunt is a web crawler optimize for search and analyze directories. This tool can find interesting things if the
server has the "index of" mode enabled. Dirhunt is also useful if the directory listing is not enabled. It detects
directories with false 404 errors, directories where an empty index file has been created to hide things and much
more.

.. code-block:: bash

    $ dirhunt http://website.com/

Dirhunt does not use brute force. But neither is it just a crawler. This tool is faster than others because it
minimizes requests to the server. Generally, this tool takes **between 5-20 seconds**, depending on the website and
the server. Features:

* Process one or multiple sites at a time.
* Process 'Index Of' pages and report interesting files.
* Detect redirectors.
* Detect blank index file created on directory to hide things.
* Process some html files in search of new directories.
* 404 error pages and detect fake 404 errors.
* Filter results by flags.


Flags
=====

Response status codes (``404``, ``200``...).

Processor key names: ``generic``, ``redirect``, ``not_found``, ``html``, ``index_of``, ``blank``.

Other: ``index_of.nothing``, ``not_found.fake``.
