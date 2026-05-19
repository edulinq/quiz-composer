import bs4

def clean(raw_html: str, pretty: bool = False) -> str:
    """
    Clean up and standardize the HTML.
    If |pretty|, then the output will be indented properly, and extra space will be stripped (which may mess with some inline spacing).
    |pretty| should only be used when being read by a human for visual inspection.
    """

    raw_html = raw_html.strip()
    if (len(raw_html) == 0):
        return ''

    document = bs4.BeautifulSoup(raw_html, 'html.parser')

    if (pretty):
        return document.prettify()

    return str(document)
