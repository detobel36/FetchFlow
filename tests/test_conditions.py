from jexflow.workflow.conditions import ConditionEvaluator


def test_condition_contains():
    item = {"title": "Coca-Cola Regular 33cl"}
    cond = {"field": "title", "operator": "contains", "value": "regular"}
    assert ConditionEvaluator.evaluate_condition(cond, item) is True

    item2 = {"title": "Coca-Cola Zero 33cl"}
    assert ConditionEvaluator.evaluate_condition(cond, item2) is False


def test_condition_not_contains():
    cond = {"field": "title", "operator": "not_contains", "value": "zero"}
    item1 = {"title": "Coca-Cola Original"}
    item2 = {"title": "Coca-Cola Zero"}
    assert ConditionEvaluator.evaluate_condition(cond, item1) is True
    assert ConditionEvaluator.evaluate_condition(cond, item2) is False


def test_condition_equals():
    cond = {"field": "category", "operator": "equals", "value": "Beverages"}
    assert ConditionEvaluator.evaluate_condition(cond, {"category": "beverages"}) is True
    assert ConditionEvaluator.evaluate_condition(cond, {"category": "Food"}) is False

    num_cond = {"field": "status", "operator": "equals", "value": 200}
    assert ConditionEvaluator.evaluate_condition(num_cond, {"status": "200"}) is True
    assert ConditionEvaluator.evaluate_condition(num_cond, {"status": 404}) is False


def test_condition_not_equals():
    cond = {"field": "type", "operator": "not_equals", "value": "out_of_stock"}
    assert ConditionEvaluator.evaluate_condition(cond, {"type": "in_stock"}) is True
    assert ConditionEvaluator.evaluate_condition(cond, {"type": "out_of_stock"}) is False


def test_condition_bigger_than():
    cond = {"field": "price", "operator": "bigger_than", "value": 10}
    assert ConditionEvaluator.evaluate_condition(cond, {"price": "15.50"}) is True
    assert ConditionEvaluator.evaluate_condition(cond, {"price": 10}) is False
    assert ConditionEvaluator.evaluate_condition(cond, {"price": 5}) is False


def test_condition_smaller_than():
    cond = {"field": "price", "operator": "smaller_than", "value": "20"}
    assert ConditionEvaluator.evaluate_condition(cond, {"price": 15}) is True
    assert ConditionEvaluator.evaluate_condition(cond, {"price": 25}) is False


def test_multiple_conditions():
    conditions = [
        {"field": "title", "operator": "contains", "value": "Coca-Cola"},
        {"field": "title", "operator": "not_contains", "value": "zero"},
        {"field": "price", "operator": "smaller_than", "value": 3},
    ]

    valid_item = {"title": "Coca-Cola Regular", "price": "2.50"}
    invalid_item_zero = {"title": "Coca-Cola Zero", "price": "2.50"}
    invalid_item_price = {"title": "Coca-Cola Regular", "price": "4.00"}

    assert ConditionEvaluator.evaluate_conditions(conditions, valid_item) is True
    assert ConditionEvaluator.evaluate_conditions(conditions, invalid_item_zero) is False
    assert ConditionEvaluator.evaluate_conditions(conditions, invalid_item_price) is False
