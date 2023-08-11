# -*- coding: utf-8 -*-

from __future__ import print_function

import asyncio
import re
import click as click
import os

import sys

from click import BadOptionUsage, Path, BadParameter, UsageError

from dirhunt.configuration import ConfigurationDict, Configuration
from dirhunt.crawler import Crawler
from dirhunt.exceptions import DirHuntError, catch, IncompatibleVersionError
from dirhunt.output import output_urls
from dirhunt.sources import SOURCE_CLASSES, get_source_name
from dirhunt.utils import (
    lrange,
    catch_keyboard_interrupt,
    force_url,
    read_file_lines,
    value_is_file_path,
    flat_list,
    multiplier_args,
    catch_keyboard_interrupt_choices,
)
from colorama import init

init(autoreset=True)

STATUS_CODES = (
    lrange(100, 102 + 1)
    + lrange(200, 208 + 1)
    + [226]
    + lrange(300, 308 + 1)
    + lrange(400, 418 + 1)
    + lrange(421, 426 + 1)
    + [428, 429, 431, 451]
    + lrange(500, 511 + 1)
)
INTERESTING_EXTS = ["php", "zip", "sh", "asp", "csv", "log"]
INTERESTING_FILES = ["access_log", "error_log", "error", "logs", "dump"]
STDOUT_FLAGS = ["blank", "not_found.fake", "html"]


def latest_release(package):
    if sys.version_info > (3,):
        from xmlrpc import client
    else:
        import xmlrpclib as client
    pypi = client.ServerProxy("https://pypi.python.org/pypi")
    available = pypi.package_releases(package)
    if not available:
        # Try to capitalize pkg name
        available = pypi.package_releases(package.capitalize())
    if not available:
        return
    return available[0]


def comma_separated(ctx, param, value):
    return (value).split(",") if value else []


def comma_separated_files(ctx, param, value):
    values = comma_separated(ctx, param, value)
    items = []
    for value in values:
        if value_is_file_path(value):
            items += read_file_lines(value)
        else:
            items.append(value)
    return items


def key_value(ctx, param, values):
    items = [item.split(":", 1) for item in values]
    if any(filter(lambda x: len(x) < 2, items)):
        raise BadParameter("Expect a value with format key:bar", ctx, param)
    return {x[0].strip(): x[1].strip() for x in items}


def status_code_range(start, end):
    return list(filter(lambda x: start <= x <= end, STATUS_CODES))


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    import dirhunt
    from dirhunt import __version__

    latest = latest_release("dirhunt")
    release = (
        "This is the latest release"
        if latest == __version__
        else "There is a new version available: {}. Upgrade it using: "
        "sudo pip install -U dirhunt".format(latest)
    )
    click.echo(
        "You are running Dirhunt v{} using Python {}.\n{}\n"
        "Installation path: {}\n"
        "Current path: {}\n".format(
            __version__,
            sys.version.split()[0],
            release,
            os.path.dirname(dirhunt.__file__),
            os.getcwd(),
        )
    )
    ctx.exit()


def welcome():
    from dirhunt import __version__

    click.secho(
        "Welcome to Dirhunt v{} using Python {}".format(
            __version__, sys.version.split()[0]
        ),
        fg="cyan",
    )


def flags_range(flags):
    for code in tuple(flags):
        match = re.match("^(\d{3})-(\d{3})$", code)
        if match:
            flags.remove(code)
            flags += list(map(str, status_code_range(*map(int, match.groups()))))
    return flags


@click.command(
    help="One or more domain or urls. Load urls from files using the /full/path or ./relative/path."
)
@click.argument("urls", nargs=-1, type=force_url)
@click.option("-t", "--threads", type=int, help="Number of threads to use.")
@click.option(
    "--concurrency",
    type=int,
    default=Configuration.concurrency,
    help="Number of concurrent requests to domains.",
)
@click.option(
    "-x",
    "--exclude-flags",
    callback=comma_separated_files,
    help="Exclude results with these flags. See documentation.",
)
@click.option(
    "-i",
    "--include-flags",
    callback=comma_separated_files,
    help="Only include results with these flags. See documentation.",
)
@click.option(
    "-e",
    "--interesting-extensions",
    callback=comma_separated_files,
    default=",".join(INTERESTING_EXTS),
    help="The files found with these extensions are interesting",
)
@click.option(
    "-f",
    "--interesting-files",
    callback=comma_separated_files,
    default=",".join(INTERESTING_FILES),
    help="The files with these names are interesting",
)
@click.option(
    "-k",
    "--interesting-keywords",
    callback=comma_separated_files,
    default="",
    help="The files with these keywords in their content are interesting",
)
@click.option(
    "--stdout-flags",
    callback=comma_separated_files,
    default=",".join(STDOUT_FLAGS),
    help="Return only in stdout the urls of these flags",
)
@click.option("--progress-enabled/--progress-disabled", default=None)
@click.option("--timeout", default=Configuration.timeout)
@click.option(
    "--max-depth",
    default=Configuration.max_depth,
    help="Maximum links to follow without increasing directories depth",
)
@click.option(
    "--not-follow-subdomains", is_flag=True, help="The subdomains will be ignored"
)
@click.option(
    "--exclude-sources",
    callback=comma_separated_files,
    help="Exclude source engines. Possible options: {}".format(
        ", ".join([get_source_name(src) for src in SOURCE_CLASSES])
    ),
)
@click.option(
    "-p",
    "--proxies",
    callback=comma_separated_files,
    help="Set one or more proxies to alternate between them",
)
@click.option(
    "-d",
    "--delay",
    default=Configuration.delay,
    type=float,
    help="Delay between requests to avoid bans by the server",
)
@click.option(
    "--not-allow-redirects", is_flag=True, help="Redirectors will not be followed"
)
@click.option(
    "--limit",
    type=int,
    default=Configuration.limit,
    help="Max number of pages processed to search for directories.",
)
@click.option(
    "--to-file",
    type=Path(writable=True),
    default=None,
    help="Create a report file in JSON.",
)
@click.option(
    "-u",
    "--user-agent",
    type=str,
    default=None,
    help="User agent to use. By default a random browser.",
)
@click.option(
    "-c",
    "--cookie",
    "cookies",
    callback=key_value,
    multiple=True,
    help="Add a cookie to requests in the cookie_name:value format.",
)
@click.option(
    "--header",
    "headers",
    callback=key_value,
    multiple=True,
    help="Add a header to requests in the header:value format.",
)
@click.option(
    "--retries",
    type=int,
    help="Retry errors the indicated number of times.",
)
@click.option(
    "--version", is_flag=True, callback=print_version, expose_value=False, is_eager=True
)
def hunt(**kwargs: ConfigurationDict):
    """Find web directories without bruteforce"""
    # Prepare configuration
    kwargs["urls"] = flat_list(kwargs["urls"])
    kwargs["proxies"] = multiplier_args(kwargs["proxies"])
    kwargs["exclude_flags"] = flags_range(kwargs["exclude_flags"])
    kwargs["include_flags"] = flags_range(kwargs["include_flags"])
    if kwargs["exclude_flags"] and kwargs["include_flags"]:
        raise UsageError("--exclude-flags and --include-flags are mutually exclusive.")
    configuration = Configuration(**kwargs)
    welcome()
    if not configuration.urls:
        click.echo(
            "•_•) OOPS! Add urls to analyze.\nFor example: dirhunt http://domain/path\n\n"
            "Need help? Then use dirhunt --help",
            err=True,
        )
        return
    loop = asyncio.get_event_loop()
    crawler = Crawler(configuration, loop)
    while True:
        try:
            loop.run_until_complete(crawler.start())
        except KeyboardInterrupt:
            click.echo("Goodbye!")
            input()
        else:
            break


def main():
    catch(hunt)()


if __name__ == "__main__":
    main()
