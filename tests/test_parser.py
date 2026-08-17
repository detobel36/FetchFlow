from scraper_engine.extraction import ElementExtractor
from scraper_engine.parser import HTMLDocument

HTML_SAMPLE = """
<html>
    <body>
        <div class="product" id="p1">
            <h2 class="title">  Widget A  </h2>
            <a href="/item/1" class="link">Details 1</a>
        </div>
        <div class="product" id="p2">
            <h2 class="title">Widget B</h2>
            <a href="/item/2" class="link">Details 2</a>
        </div>
    </body>
</html>
"""


def test_html_parsing_and_css_extraction():
    doc = HTMLDocument(HTML_SAMPLE)

    # CSS extract containers
    containers = ElementExtractor.extract_nodes(doc, ".product", selector_type="css")
    assert len(containers) == 2

    # Extract title text from first container
    titles = ElementExtractor.extract_field_values(containers[0], ".title", selector_type="css",
                                                   extraction_type="text")
    assert titles == ["  Widget A  "]

    # Extract href attribute from link
    links = ElementExtractor.extract_field_values(containers[0], "a.link", selector_type="css",
                                                  extraction_type="attribute", attribute="href")
    assert links == ["/item/1"]


def test_xpath_extraction():
    doc = HTMLDocument(HTML_SAMPLE)

    titles = ElementExtractor.extract_field_values(doc, "//h2[@class='title']", selector_type="xpath",
                                                   extraction_type="text")
    assert titles == ["  Widget A  ", "Widget B"]

    attrs = ElementExtractor.extract_field_values(doc, "//a/@href", selector_type="xpath")
    assert attrs == ["/item/1", "/item/2"]


LIST_SAMPLE = """
<html>
    <body>
        <ul class="items">
            <li>First Item</li>
            <li>Second Item</li>
            <li>Third Item</li>
            <li>Fourth Item</li>
        </ul>
    </body>
</html>
"""


def test_css_nth_element_selection():
    doc = HTMLDocument(LIST_SAMPLE)

    nth_child_3 = ElementExtractor.extract_field_values(
        doc, "ul.items > li:nth-child(3)", selector_type="css", extraction_type="text",
    )
    assert nth_child_3 == ["Third Item"]

    nth_type_3 = ElementExtractor.extract_field_values(
        doc, "ul.items > li:nth-of-type(3)", selector_type="css", extraction_type="text",
    )
    assert nth_type_3 == ["Third Item"]


def test_xpath_nth_element_selection():
    doc = HTMLDocument(LIST_SAMPLE)

    xpath_3 = ElementExtractor.extract_field_values(
        doc, "//ul[@class='items']/li[3]", selector_type="xpath", extraction_type="text",
    )
    assert xpath_3 == ["Third Item"]
