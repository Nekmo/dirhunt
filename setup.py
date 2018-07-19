#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Package description
"""
from setuptools import setup, find_packages, __version__ as setuptool_version
from distutils.version import StrictVersion
from distutils.util import convert_path
from fnmatch import fnmatchcase
import os
import sys


###############################
#  Configuración del paquete  #
###############################

# Información del autor
AUTHOR = 'Nekmo'
EMAIL = 'contacto@nekmo.com'

# Información del paquete
PACKAGE_NAME = 'dirhunt'
PACKAGE_DOWNLOAD_URL = 'https://github.com/Nekmo/dirhunt/archive/master.zip'  # .tar.gz
REQUIREMENTS_FILES = [
    {'name': 'common-requirements.txt'},
    {'name': 'py2-requirements.txt', 'marker': 'python_version<"3.0"', "include": sys.version_info < (3,0)},
    {'name': 'py3-requirements.txt', 'marker': 'python_version>"3.0"', "include": sys.version_info > (3,0)},
]
URL = 'https://github.com/Nekmo/dirhunt'
STATUS_LEVEL = 3  # 1:Planning 2:Pre-Alpha 3:Alpha 4:Beta 5:Production/Stable 6:Mature 7:Inactive
KEYWORDS = ['directories', 'websec', 'pentesting', 'security-audit']  # Palabras clave
# https://github.com/github/choosealicense.com/tree/gh-pages/_licenses
CLASSIFIERS = [
    # Common licenses
    'License :: OSI Approved :: MIT License',
    # 'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
    # 'License :: OSI Approved :: BSD License',
]  # https://pypi.python.org/pypi?%3Aaction=list_classifiers
NATURAL_LANGUAGE = 'English'  # English...

# Requerido para la correcta instalación del paquete
PLATFORMS = [
    # 'universal',
    'linux',
    # 'macosx',
    # 'solaris',
    # 'irix',
    # 'win'
    # 'bsd'
    # 'ios'
    # 'android'
]
ROOT_INCLUDE = [
    'requirements.txt',
    'common-requirements.txt',
    'py2-requirements.txt',
    'py3-requirements.txt',
    'VERSION',
    'LICENSE.txt'
]
PYTHON_VERSIONS = ['2.7', '3.4-3.7']

######## FIN DE LA CONFIGURACIÓN DEL PAQUTE ########

__author__ = AUTHOR
__dir__ = os.path.abspath(os.path.dirname(__file__))

# paths
readme_path = os.path.join(__dir__, 'README')
if not os.path.exists(readme_path):
    readme_path = os.path.join(__dir__, 'README.rst')
version_path = os.path.join(__dir__, 'VERSION')
requirements_path = os.path.join(__dir__, 'py{}-requirements.txt'.format(sys.version_info.major))
scripts_path = os.path.join(__dir__, 'scripts')


def get_url(ir):
    if hasattr(ir, 'url'): return ir.url
    if ir.link is None: return
    return ir.link.url


##############################################################################
# find_package_data is an Ian Bicking creation.

# Provided as an attribute, so you can append to these instead
# of replicating them:
standard_exclude = ('*.py', '*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build',
                                './dist', 'EGG-INFO', '*.egg-info')


def find_package_data(where='.', package='',
                      exclude=standard_exclude,
                      exclude_directories=standard_exclude_directories,
                      only_in_packages=True,
                      show_ignored=False):
    """
    Return a dictionary suitable for use in ``package_data``
    in a distutils ``setup.py`` file.

    The dictionary looks like::

        {'package': [files]}

    Where ``files`` is a list of all the files in that package that
    don't match anything in ``exclude``.

    If ``only_in_packages`` is true, then top-level directories that
    are not packages won't be included (but directories under packages
    will).

    Directories matching any pattern in ``exclude_directories`` will
    be ignored; by default directories with leading ``.``, ``CVS``,
    and ``_darcs`` will be ignored.

    If ``show_ignored`` is true, then all the files that aren't
    included in package data are shown on stderr (for debugging
    purposes).

    Note patterns use wildcards, or can be exact paths (including
    leading ``./``), and all searching is case-insensitive.

    This function is by Ian Bicking.
    """

    out = {}
    stack = [(convert_path(where), '', package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            sys.stderr.write(
                                "Directory %s ignored by pattern %s\n"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                    stack.append((fn, '', new_package, False))
                else:
                    stack.append(
                        (fn, prefix + name + '/', package, only_in_packages)
                    )
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            sys.stderr.write(
                                "File %s ignored by pattern %s\n"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix + name)
    return out


##############################################################################

def read_requirements_file(path):
    if not os.path.lexists(path):
        return
    with open(path) as f:
        lines = f.readlines()
    for line in lines:
        line = line.split('#', 1)[0]
        line = line.strip()
        if line.startswith('-'):
            continue
        yield line


def read_requirements_files(files):
    reqs = []
    for file in files:
        if StrictVersion(setuptool_version) >= StrictVersion('20.2'):
            reqs.extend([('{};{}'.format(req, file['marker']) if file.get('marker') else req)
                         for req in read_requirements_file(file['name'])])
        elif file.get('include', True):
            # Retrocompatibility mode for setuptools < 20.2
            reqs.extend(list(read_requirements_file(file['name'])))
    return reqs


# Todos los módulos y submódulos a instalar (module, module.submodule, module.submodule2...)
packages = find_packages(__dir__)
# Prevent include symbolic links
for package in tuple(packages):
    path = os.path.join(__dir__, package.replace('.', '/'))
    if not os.path.exists(path):
        continue
    if not os.path.islink(path):
        continue
    packages.remove(package)

# Otros archivos que no son Python y que son requeridos
package_data = {'': ROOT_INCLUDE}

# Obtener la lista de módulos que se instalarán
modules = list(filter(lambda x: '.' not in x, packages))

for module in modules:
    package_data.update(find_package_data(
        module,
        package=module,
        only_in_packages=False,
    ))

# Descripción larga si existe un archivo README
try:
    long_description = open(readme_path, 'rt').read()
except IOError:
    long_description = ''

# Tomar por defecto la versión de un archivo VERSION. Si no, del módulo
if os.path.exists(version_path):
    package_version = open(version_path).read().replace('\n', '')
else:
    package_version = __import__(modules[0]).__version__

# Si hay un directorio scripts, tomar todos sus archivos
if os.path.exists(scripts_path):
    scripts_dir_name = scripts_path.replace(__dir__, '', 1)
    scripts_dir_name = scripts_dir_name[1:] if scripts_dir_name.startswith(os.sep) else scripts_dir_name
    scripts = [os.path.join(scripts_dir_name, file) for file in os.listdir(scripts_path)]
else:
    scripts = []

# Eliminar archivos de ROOT_INCLUDE que no existen
for d in tuple(ROOT_INCLUDE):
    if not os.path.exists(os.path.join(__dir__, d)):
        ROOT_INCLUDE.remove(d)

# Nombre del estado de desarrollo
status_name = ['Planning', 'Pre-Alpha', 'Alpha', 'Beta',
               'Production/Stable', 'Mature', 'Inactive'][STATUS_LEVEL - 1]

# Añadir en los classifiers la plataforma
platforms_classifiers = {'linux': ('POSIX', 'Linux'), 'win': ('Microsoft', 'Windows'),
                         'solaris': ('POSIX', 'SunOS/Solaris'), 'aix': ('POSIX', 'Linux'), 'unix': ('Unix',),
                         'bsd': ('POSIX', 'BSD')}
for key, parts in platforms_classifiers.items():
    if not key in PLATFORMS:
        continue
    CLASSIFIERS.append('Operating System :: {}'.format(' :: '.join(parts)))


# Añadir la versión de Python a los Classifiers
def frange(x, y, jump):
    while x < y:
        yield x
        x += jump


python_versions = []
for version in PYTHON_VERSIONS:
    if '-' in version:
        version = version.split('-')
        if len(version) != 2:
            raise ValueError('Invalid Python version range: {}'.format('-'.join(version)))
        version = list(map(float, version))
        version[1] += 0.1  # Para que frange incluya la última versión
        python_versions.extend(frange(version[0], version[1], 0.1))
    elif isinstance(version, int) or version.isdigit():
        python_versions.append(str(version))
    else:
        python_versions.append(float(version))
python_versions = map(lambda x: x if isinstance(x, str) else '%.1f' % x, python_versions)
# Eliminar versiones 0-2.3 y 2.8-2.9
remove_python_versions = map(str, list(frange(0, 2.3, 0.1)) + list(frange(2.8, 3.0, 0.1)))
python_versions = list(filter(lambda x: x not in remove_python_versions, python_versions))
for version in range(2, 4):
    if not len(list(filter(lambda x: int(float(x)) != version, python_versions))):
        # Sólo se encuentran versiones para la versión <version>
        python_versions.append('%i :: Only' % version)
        break
CLASSIFIERS.extend(['Programming Language :: Python :: %s' % version for version in python_versions])

CLASSIFIERS.extend([
    'Natural Language :: {}'.format(NATURAL_LANGUAGE),
    'Development Status :: {} - {}'.format(STATUS_LEVEL, status_name),
])

setup(
    name=PACKAGE_NAME,
    version=package_version,

    description=__doc__,
    long_description=long_description,

    author=AUTHOR,
    author_email=EMAIL,

    url=URL,

    classifiers=CLASSIFIERS,

    platforms=PLATFORMS,

    provides=modules,
    install_requires=read_requirements_files(REQUIREMENTS_FILES),

    packages=packages,
    include_package_data=True,
    # Scan the input for package information
    # to grab any data files (text, images, etc.)
    # associated with sub-packages.
    package_data=package_data,

    download_url=PACKAGE_DOWNLOAD_URL,
    keywords=KEYWORDS,
    scripts=scripts,

    # entry_points={},

    zip_safe=False,
)
