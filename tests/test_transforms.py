from jexflow.transforms import TransformerRegistry


def test_trim_lower_upper():
    res = TransformerRegistry.apply_pipeline(["  HELLO World  "], ["trim", "lower"])
    assert res == ["hello world"]

    res_upper = TransformerRegistry.apply_pipeline(["hello"], ["upper"])
    assert res_upper == ["HELLO"]


def test_replace():
    res = TransformerRegistry.apply_pipeline(
        ["12,345.67"],
        [{"replace": {"from": ",", "to": ""}}],
    )
    assert res == ["12345.67"]


def test_split():
    res = TransformerRegistry.apply_pipeline(
        ["a,b,c"],
        [{"split": ","}, "trim", "upper"],
    )
    assert res == ["A", "B", "C"]


def test_regex():
    res = TransformerRegistry.apply_pipeline(
        ["Price: $19.99 USD"],
        [{"regex": "([0-9,.]+)"}],
    )
    assert res == ["19.99"]


def test_url_encode():
    res = TransformerRegistry.apply_pipeline(
        ["hello world & foo=bar"],
        ["url_encode"],
    )
    assert res == ["hello%20world%20%26%20foo%3Dbar"]

    res_alias = TransformerRegistry.apply_pipeline(
        ["hello world & foo=bar"],
        ["urlencode"],
    )
    assert res_alias == ["hello%20world%20%26%20foo%3Dbar"]


def test_url_decode():
    res = TransformerRegistry.apply_pipeline(
        ["hello%20world%20%26%20foo%3Dbar"],
        ["urldecode"],
    )
    assert res == ["hello world & foo=bar"]


def test_url_join():
    res = TransformerRegistry.apply_pipeline(
        ["/path/to/page"],
        [{"urljoin": "https://example.com/base/"}],
    )
    assert res == ["https://example.com/path/to/page"]

    res_dict = TransformerRegistry.apply_pipeline(
        ["subpage.html"],
        [{"urljoin": {"base": "https://example.com/docs/"}}],
    )
    assert res_dict == ["https://example.com/docs/subpage.html"]


def test_parse_url():
    res_netloc = TransformerRegistry.apply_pipeline(
        ["https://user:pass@example.com:8080/path/to/resource?a=1#section"],
        [{"parse_url": "netloc"}],
    )
    assert res_netloc == ["user:pass@example.com:8080"]

    res_path = TransformerRegistry.apply_pipeline(
        ["https://example.com/path/to/resource"],
        [{"parse_url": {"component": "path"}}],
    )
    assert res_path == ["/path/to/resource"]


def test_query_param():
    res = TransformerRegistry.apply_pipeline(
        ["https://example.com/search?q=test&category=books&q=override"],
        [{"query_param": "q"}],
    )
    assert res == ["test", "override"]

    res_single = TransformerRegistry.apply_pipeline(
        ["https://example.com/search?category=books"],
        [{"query_param": "category"}],
    )
    assert res_single == ["books"]

    res_missing = TransformerRegistry.apply_pipeline(
        ["https://example.com/search?category=books"],
        [{"query_param": "nonexistent"}],
    )
    assert res_missing == [""]


def test_base64_encode_decode():
    encoded = TransformerRegistry.apply_pipeline(
        ["hello world!"],
        ["base64_encode"],
    )
    assert encoded == ["aGVsbG8gd29ybGQh"]

    decoded = TransformerRegistry.apply_pipeline(
        encoded,
        ["base64_decode"],
    )
    assert decoded == ["hello world!"]


def test_html_encode_decode():
    encoded = TransformerRegistry.apply_pipeline(
        ['<script>alert("xss & hello")</script>'],
        ["html_encode"],
    )
    assert encoded == ["&lt;script&gt;alert(&quot;xss &amp; hello&quot;)&lt;/script&gt;"]

    decoded = TransformerRegistry.apply_pipeline(
        encoded,
        ["html_decode"],
    )
    assert decoded == ['<script>alert("xss & hello")</script>']


def test_space_to_dash():
    res = TransformerRegistry.apply_pipeline(
        ["like this for exemple"],
        ["space_to_dash"],
    )
    assert res == ["like-this-for-exemple"]
