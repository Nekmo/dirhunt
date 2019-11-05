.. highlight:: console

============
Installation
============


Stable release
--------------

To install Dirhunt, run this command in your terminal:

.. code-block:: console

    $ pip install dirhunt

This is the preferred method to install Dirhunt, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


Other releases
--------------
You can install other versions from Pypi using::

    $ pip install dirhunt==<version>

For versions that are not in Pypi (it is a development version)::

    $ pip install git+https://github.com/Nekmo/dirhunt@<branch>#egg=dirhunt


Optional dependencies
---------------------
These dependencies are required to use **SOCKS proxies**::

    pip3 install 'urllib3[socks]'


From sources
------------

The sources for Dirhunt can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/Nekmo/dirhunt

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/Nekmo/dirhunt/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install


.. _Github repo: https://github.com/Nekmo/dirhunt
.. _tarball: https://github.com/Nekmo/dirhunt/tarball/master
