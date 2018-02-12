

def output_urls(crawler, stdout_flags):
    crawler_urls = filter(lambda x: x.maybe_directory(), crawler.processed.values())
    for crawler_url in sorted(crawler_urls, key=lambda x: x.weight(), reverse=True):
        print(crawler_url.url.address)
