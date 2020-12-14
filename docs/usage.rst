.. highlight:: console


=====
Usage
=====

To see the available help run::

    $ dirhunt --help


.. click:: dirhunt.management:hunt
   :prog: dirhunt
   :show-nested:


Find directories
----------------
You can define one or more urls/domains, from the same domain or different. It is better if you put urls with complete
paths. This way Dirhunt will have easier to find directories.

.. code::

    $ dirhunt <url 1>[ <url 2>]

For example::

    $ dirhunt http://domain1/blog/awesome-post.html http://domain1/admin/login.html http://domain2/ domain3.com


Results for multiple sites will be displayed together. You can also load urls or domains from one or more files using
 the full path (/path/to/file) or the relative path (./file). Examples::

    dirhunt domain1.com ./file/to/domains.txt /home/user/more_domains.txt


Resume analysis
---------------
Press ``Ctrl + c`` to pause the current scan. For example::


    ...
    [200] https://site.com/path/  (Generic)
        Index file found: index.php
    [200] https://site.com/path/foo/  (Generic)
        Index file found: index.php
    ◣ Started a second ago
    ^C

    An interrupt signal has been detected. what do you want to do?

      [A]bort
      [c]ontinue
      [r]esults
    Enter a choice [A/c/r]:


You can continue the analysis now (choose option ``c`` ), show the current results (press ``r`` ) or
abort now. Run the analysis again with the same parameters to pick the analysis where you left off.

.. code-block:: text

    An interrupt signal has been detected. what do you want to do?

      [A]bort
      [c]ontinue
      [r]esults
    Enter a choice [A/c/r]: A
    Created resume file "/home/nekmo/.cache/dirhunt/ca32...". Run again using the same parameters to resume.


Save results to file
--------------------
Use the ``--to-file`` option to create a JSON file with the results. The file is created even if you abort the
current analysis. You can continue an aborted scan using the ``--to-file`` parameter again. The syntax is:

.. code-block::

    $ dirhunt <url> --to-file <json file>

For example::

    $ dirhunt http://domain1/blog/ --to-file report.json

Report example:

.. code-block:: json

    {
        "version": "0.7.0",
        "current_processed_count": 10,
        "domains": [
            "localhost"
        ],
        "index_of_processors": [
            {
                "crawler_url": {
                    "depth": -1,
                    "exists": true,
                    "flags": [
                        "200",
                        "index_of"
                    ],
                    "type": "directory",
                    "url": {
                        "address": "http://localhost/foo/img/",
                        "domain": "localhost"
                    }
                },
                "line": "...",
                "processor_class": "ProcessIndexOfRequest",
                "status_code": 200
            }
        ],
        "processed": [
            {
                "crawler_url": {
                    "depth": 3,
                    "exists": null,
                    "flags": [
                        "404",
                        "not_found"
                    ],
                    "type": null,
                    "url": {
                        "address": "http://localhost/folder1/",
                        "domain": "localhost"
                    }
                },
                "line": "...",
                "processor_class": "ProcessNotFound",
                "status_code": 404
            }
        ],
        "processing": [
            "http://localhost/other/"
        ],
        "urls_infos": [
            {
                "data": {
                    "body": null,
                    "resp": {
                        "headers": {
                            "Accept-Ranges": "bytes",
                            "Connection": "keep-alive",
                            "Content-Length": "24",
                            "Content-Type": "application/octet-stream",
                            "Date": "Mon, 27 Apr 2020 22:57:23 GMT",
                            "ETag": "\"5ea76330-18\"",
                            "Last-Modified": "Mon, 27 Apr 2020 22:56:48 GMT",
                            "Server": "nginx/1.16.1"
                        },
                        "status_code": 200
                    },
                    "text": " This is a hack script!\n",
                    "title": null
                },
                "text": "This is a hack script!",
                "url": {
                    "address": {
                        "address": "http://localhost/foo/img/",
                        "domain": "localhost"
                    },
                    "domain": "localhost"
                }
            }
        ]
    }

Sections in the report:

* **version**: Dirhunt version of the report. It is only possible to resume an analysis of the same version of Dirhunt.
* **current_processed_count**: number of urls processed during the analysis.
* **domains**: domains added to the analysis.
* **index_of_processors**: urls processed of type *index of*.
* **processed**: other urls processed during the analysis.
* **processing**: urls found but not processed. There are only urls to process in case of aborting the analysis.
* **urls_infos**: info about the detected urls.


Interesting extensions
----------------------
By default, Dirhunt will notify you if it find one of these extension file names: ``php``, ``zip``, ``sh``, ``asp``,
``csv`` and ``log``. You can change these extensions using the parameter ``--interesting-extensions`` (``-e``).
The files found with these extensions will be shown as they are discovered.

.. code::

    $ dirhunt <url> -e <ext 1>[,<ext 2>]

For example::

    $ dirhunt http://domain1/blog/ -e php,zip,sh

It is also possible to read extensions from files. `See "Comma separated files" <#id3>`_.


Interesting files
-----------------
Dirhunt can warn you if it finds a specific file name. By default Dirhunt will warn you if you find one of these files:
``access_log``, ``error_log``, ``error``, ``logs``, ``dump``. You can change these files using the parameter
``--interesting-files`` (``-f``). The files found will be shown as they are discovered.

.. code::

    $ dirhunt <url> -f <name 1>[,<name 2>]

For example::

    $ dirhunt http://domain1/blog/ -f access_log,error_log

You can also load file names from one or more local files::

    $ dirhunt http://domain1/blog/ -f /home/user/dict.txt,./files.txt

You can read more about this `here <#id3>`_


Exclude
-------
Filter the results using the ``--exclude-flags`` (``-x``) parameter (see the `flags section <#Flags>`_ to
see how you can filter the results).

.. code::

    $ dirhunt <url> -x <flags comma separated>

For example::

    $ dirhunt http://domain1/blog/ -x http,not_found,index_of.nothing,300-500

It is also possible to read excludes from files. See `"Comma separated files" <#id3>`_


Include
-------
This is the opposite to *exclude*. ``--include-flags`` (``-i``) allows you to show only the
results that are in the defined flags::

    $ dirhunt <url> -i <flags comma separated>

For example::

    $ dirhunt http://domain1/blog/ -i html,300-500

See the `flags section <#Flags>`_ to see how you can filter the results.

It is also possible to read includes from files. See `"Comma separated files" <#id3>`_


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


Threads
-------
Dirhunt makes multiple simultaneous requests using threads by default. The default number of threads is
``cpu count * 5``. If you use the ``--delay`` option, the *simultaneous requests mode* is disabled and the number of
threads by default is ``number of proxies``. If you do not use proxies in ``--delay`` mode, the default threads
number is 1. You can change the threads count using ``--threads <count>`` (``-t <count>``). Usage::

    $ dirhunt <url> --threads <count>

For example::

    $ dirhunt http://domain1/blog/ --threads 10


Delay
-----
This mode deactivates *simultaneous requests mode* and it activates a waiting time from the end of a request
and the next one begins. By default delay is **disabled**. Use this mode only if the server is restricting requests.
You can improve the performance of this option using multiple proxies. Usage::

    $ dirhunt <url> --delay <float>

For example::

    $ dirhunt http://domain1/blog/ --delay 0.1


Proxies
-------
You can use one or multiple proxies for your requests using ``--proxies`` option. Dirhunt will balance the load
between proxies. If you are not restricting requests using ``--delay`` option then dirhunt will use the proxy that is
not in use. If there is no free proxy available then dirhunt will use a random proxy. Usage::

    $ dirhunt <url> --proxies <proxy 1>[, <proxy 2>]

If you use "none" as a proxy then Dirhunt will not use a proxy. This is useful if you want to combine
proxies and your real internet connection. For example::

    $ dirhunt http://domain1/blog/ --proxies http://localhost:3128,none


Dirhunt includes an alias called ``tor`` for ``socks5://127.0.0.1:9150``. For example::

    $ dirhunt http://domain1/blog/ --proxies tor


Dirhunt can also search for free proxies thanks to `proxy-db <https://github.com/Nekmo/proxy-db>`_. This library
creates a database of proxies that scores. To use a free proxy use `random`::

    $ dirhunt http://domain1/blog/ --proxies random


To avoid being banned you can switch between several proxies. For example::

    $ dirhunt http://domain1/blog/ --proxies random*8


You can also use a proxie from a country. `Here <https://dev.maxmind.com/geoip/legacy/codes/iso3166/>`_ is a
complete list of countries. For example to navigate from Spain::

    $ dirhunt http://domain1/blog/ --proxies es

The proxies option allows you to improve the performance of the ``--delay`` option. The delay time is independent
for each proxy. Use multiple proxies to improve your scan. You can repeat the same proxy several times to allow
multiple requests from the same proxy when the delay option is used. You can also repeat a proxy several times
to increase the use of a proxy. A shortcut to repeating a proxy is to use the mult operator (*). For example::

    $ dirhunt http://domain1/blog/ --proxies http://localhost:3128,tor*8


Timeout
-------
By default Dirhunt only waits up to 10 seconds for each url. You can increase or decrease this time using
``--timeout``::

    $ dirhunt <url> --timeout <seconds>

For example::

    $ dirhunt http://domain1/blog/ --timeout 15


Max follow links depth
----------------------
Maximum links to follow without increasing directories depth. By default 3. For example in redirects
``/index.php > /about.php > /map.php > /contactus.php`` the last page can not redirect to another page at the same
directory level because it has exceeded the default limit of 3. Usage::

    $ dirhunt <url> --max-depth <number>

For example::

    $ dirhunt http://domain1/blog/ --max-depth 3


Limit
-----
Dirhunt follows links on the page to obtain directories. In addition to the ``--max-depth`` limit, there is a
maximum of pages processed for find links. The default limit is 1000 but can be changed using ``--limit <number>``.
To deactivate the limit (unlimited) use zero: ``--limit 0``. Usage::

    $ dirhunt <url> --limit <number>

For example::

    $ dirhunt http://domain1/blog/ --limit 2000


Not follow subdomains
---------------------
Dirhunt by default will follow all the subdomains of the domain urls. For example if Dirhunt finds webmail.site.com
on site.com dirhunt will follow the link. You can disable this feature using the flag ``--not-follow-subdomains``.
Usage::

    $ dirhunt <url> --not-follow-subdomains

For example::

    $ dirhunt http://domain1/blog/ --not-follow-subdomains


Exclude sources
---------------
Dirhunt by default will get urls from different sources. You can disable some or all of the engines using the
``--exclude-sources`` option. Usage::

    $ dirhunt <url> --exclude-sources <sources comma separated>

For example::

    $ dirhunt http://domain1/blog/ --exclude-sources robots,virustotal


Not allow redirectors
----------------------
Dirhunt by default will follow redirectors within the website (HTTP Redirectors). You can disable this feature using
the flag ``--not-allow-redirectors``. Usage::

    $ dirhunt <url> --not-allow-redirectors

For example::

    $ dirhunt http://domain1/blog/ --not-allow-redirectors


Comma separated files
---------------------
In those parameters with arguments separated by commas, it is possible to read values from one or more local files.

.. code::

    $ dirhunt <url> --<parameter> <file 1>,<file 2>

Example for **interesting files** (``-f``)::

    $ dirhunt http://domain1/blog/ -f /path/to/file1.txt,./file2.txt

It is necessary to put the complete path to the file, or the relative using ``./``. Each value of the files must be
separated by newlines.

Custom headers
--------------
To add custom HTTP headers to requests you can use the ``--header`` parameter.

.. code::

    $ dirhunt <url> --header <Field name>:<Field value>

This parameter can be used more than once, for example::

    $ dirhunt http://domain1/blog/ --header "Authorization: token foo" --header "X-Server: prod"


Custom cookies
--------------
To add custom cookies to requests you can use the ``--cookie`` parameter.

.. code::

    $ dirhunt <url> --cookie <Cookie name>:<Cookie value>

This parameter can be used more than once, for example::

    $ dirhunt http://domain1/blog/ --cookie "session: secret" --cookie "user: 123"


Progress bar
------------
By default Dirhunt displays a progress bar while loading results if possible. If the progress bar causes problems, you
can disable it using ``--progress-disabled``. By default ``--progress-enabled``.

.. code::

    $ dirhunt <url> --progress-disabled

For example::

    $ dirhunt http://domain1/blog/ --progress-disabled


Version
-------
To see the Dirhunt installed version se ``--version``::

    $ dirhunt --version
    You are running Dirhunt v0.3.0 using Python 3.6.3.
    This is the latest release
    Installation path: /home/nekmo/Workspace/dirhunt/dirhunt
    Current path: /home/nekmo/Workspace/dirhunt


If you have issues with Dirhunt and you are going to open a ticket, paste this output on the issue.
Also use this command to see if Dirhunt is out of date.

.. code::

    $ dirhunt --version
    You are running Dirhunt v0.3.0 using Python 3.6.5.
    There is a new version available: 0.4.0. Upgrade it using: sudo pip install -U dirhunt
    Installation path: /home/nekmo/Workspace/dirhunt/dirhunt
    Current path: /home/nekmo/Workspace/dirhunt


External programs
-----------------
Folders that have been found can be redirected to the standard output::

    dirhunt www.domain.com/path > directories.txt

You can use standard output to run other programs to use brute force::

    for url in $(dirhunt www.domain.com/path); do
        other.py -u "$url";
    done

You can define the type of results that will be returned using flags::

    dirhunt www.domain.com/path --stdout-flags blank,not_found.fake,html > directories.txt
