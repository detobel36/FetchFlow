from scraper_engine.transforms import TransformerRegistry


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
