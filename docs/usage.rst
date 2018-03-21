.. highlight:: console


=====
Usage
=====

To see the available help run::

    $ dirhunt --help


Example::

    Usage: dirhunt [OPTIONS] [URLS]...

      :type exclude_flags: list

    Options:
      -x, --exclude-flags TEXT        Exclude results with these flags. See
                                      documentation.
      -e, --interesting-extensions TEXT
                                      The files found with these extensions are
                                      interesting
      -f, --interesting-files TEXT    The files with these names are interesting
      --help                          Show this message and exit.



Find directories
----------------
You can define one or more urls, from the same domain or different. It is better if you put urls with complete
routes. This way Dirhunt will have easier to find directories.

.. code::

    $ dirhunt <url 1>[ <url 2>]

For example::

    $ dirhunt http://domain1/blog/awesome-post.html http://domain1/admin/login.html http://domain2/


Interesting extensions
----------------------
By default, Dirhunt will notify you if it find one of these extension file names: ``php``, ``zip``, ``sh``, ``asp``,
``csv`` and ``log``. You can change these extensions using the parameter ``--interesting-extensions`` (``-e``).
The files found with these extensions will be shown as they are discovered.

.. code::

    $ dirhunt <url> -e <ext 1>[,<ext 2>]

For example::

    $ dirhunt http://domain1/blog/ -e php,zip,sh

It is also possible to read extensions from files. `See "Comma separated files" <#comma-separated-files>`_.


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

You can read more about this `here <#comma-separated-files>`_


Exclude
-------
Filter the results using the ``--exclude-flags`` (``-x``) parameter.

.. code::

    $ dirhunt <url> -x <flags comma separated>

For example::

    $ dirhunt http://domain1/blog/ -x http,not_found,index_of.nothing,300-500

See the `flags section <#Flags>`_ to see how you can filter the results.

It is also possible to read excludes from files. See "Comma separated files"

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


Comma separated files
---------------------
In those parameters with arguments separated by commas, it is possible to read values from one or more local files.

.. code::

    $ dirhunt <url> --<parameter> <file 1>,<file 2>

Example for **interesting files** (``-f``)::

    $ dirhunt http://domain1/blog/ -f /path/to/file1.txt,./file2.txt

It is necessary to put the complete path to the file, or the relative using ``./``. Each value of the files must be
separated by newlines.


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
