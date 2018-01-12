
Dirhunt
#######
Dirhunt is a web crawler optimize for search and analyze directories. This tool can find interesting things if the
server has the "index of" mode enabled. Dirhunt is also useful if the directory listing is not enabled. It detects
directories with false 404 errors, directories where an empty index file has been created to hide things and much
more.

.. code-block:: bash

    $ dirhunt http://website.com/

Dirhunt does not use brute force. But neither is it just a crawler. This tool is faster than others because it
minimizes requests to the server. Generally, this tool takes **between 5-30 seconds**, depending on the website and
the server. Features:

* Process one or multiple sites at a time.
* Process 'Index Of' pages and report interesting files.
* Detect redirectors.
* Detect blank index file created on directory to hide things.
* Process some html files in search of new directories.
* 404 error pages and detect fake 404 errors.
* Filter results by flags.


Install
=======
If you have Pip installed on your system, you can use it to install Dirhunt::

    $ sudo pip3 install dirhunt

At this time only Python 3.4+ is officially supported. Other versions may work but without guarantees.


Usage
=====
You can define one or more urls, from the same domain or different. It is better if you put urls with complete
routes. This way Dirhunt will have easier to find directories.

.. code-block:: bash

    $ dirhunt <url 1>[ <url 2>]

For example::

    $ dirhunt http://domain1/blog/awesome-post.html http://domain1/admin/login.html http://domain2/


Exclude
-------
Filter the results using the ``--exclude-flags`` (``-x``) parameter.

.. code-block:: bash

    $ dirhunt <url> -x <flags comma separated>

For example::

    $ dirhunt http://domain1/blog/ -x http,not_found,index_of.nothing,300-500

See the flags section to see how you can filter the results.


Flags
-----
The results are cataloged with one or several flags. Results with a **status code** include a flag with the status
number. For example, a successful response with status code ``200`` includes as flag ``200``. When filtered, ranges
of response codes can be defined. For example, ``401-500``.

The processor used to process the result is also included as a flag. The names of the processors are:

* ``generic``
* ``redirect``
* ``not_found``
* ``html``
* ``index_of``
* ``blank``

Also, some processors may have some extra flags:

* ``index_of.nothing``: 'Index Of' without interesting files.
* ``not_found.fake``: Fake 404 directory.

Other flags:

* ``wordpress``: The page belongs to a wordpress.
