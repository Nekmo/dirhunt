=======
History
=======

0.8.0 (2020-12-14)
------------------

* Meta refresh tag not considered (issue #71)
* Use sphinx-click for docs (issue #80)
* Random user agent by default (issue #78)
* Cli parameter to set the user agent (issue #79)
* Check javascript files for dirhunt (issue #69)
* custom Header/Cookie (issue #84)


0.7.0 (2020-04-28)
------------------

* Report to file (issue #62)
* Resume scan after close Dirhunt (issue #53)
* Option to stop analysis and go to results by pressing ctrl+c (issue #61)
* Process CSS files (issue #84)
* Catch None in function is_url_loop (issue #66)
* Exclude sources from tests (issue #67)
* Missing dependencies for SOCKS support (issue #72)
* Test Python 3.8 on Travis (issue #74)
* Remove Python 3.4 support (issue #75)


0.6.0 (2018-11-01)
------------------

* Search on Google (issue #2)
* Find and use free random proxies (issue #33)
* Extract dates and match different date files (issue #26)
* Limit of processed pages (issue #51 & issue #52)
* Mult operator (*) in argument proxies (issue #55)
* Switch for domain list (issue #39)
* WARNING:urllib3.connectionpool:Connection pool is full, discarding connection (isse #56)
* TypeError: 'NoneType' object is not subscriptable in url.py, line 147 (issue #57)
* Catch UrlInfo read exceptions (issue #58)
* Error in resp.raw.read(MAX_RESPONSE_SIZE, decode_content=True) (issue #59)


0.5.0 (2018-09-04)
------------------

* Command not found issue for Windows (issue #40)
* Search on VirusTotal (issue #31)
* Delay between requests (issue #14 & issue #48)
* Set proxies (issue #32 & issue #47)
* Tor proxy alias (issue #49)


0.4.0 (2018-07-23)
------------------

* Use robots.txt (issue #1)
* Detect and mitigate recursion loops (issue #23)
* Improved installation process compatibility (issue #35)
* Python 3.7 compatibility (issue #34)
* Option ``--not-allow-redirects`` (issue #15)
* Option ``--not-follow-subdomains`` (issue #16)
* Option ``--max-depth`` to follow link (issue #17)


0.3.0 (2018-04-16)
------------------

* Include option: ``--include-flags`` (issue #13)
* Option ``--timeout`` (issue #19)
* List all file results at end (issue #20)
* Unit testing (issue #21)
* Support Python 2.7 (issue #22)
* Travis configuration (issue #24)
* Add and change console colors (issues #25 & #28)
* Better documentation (issue #27)
* Dirhunt version (issue #29)
* Error on urls undefined (issue #30)


0.2.0 (2018-02-13)
------------------

* docs.nekmo.org documentation (issue #9)
* Change threads number option (issue #7)
* Enable/disable progress (issue #18)
* Accessibility to enter urls (issues #4 and #12)
* Resolved multiple bugs (issues #5, #6, #8 and #10)
* Directories found to stdout (issue #11)


0.1.0 (2018-01-12)
------------------

* Process one or multiple sites at a time.
* Process 'Index Of' pages and report interesting files.
* Detect redirectors.
* Detect blank index file created on directory to hide things.
* Process some html files in search of new directories.
* 404 error pages and detect fake 404 errors.
* Filter results by flags.
