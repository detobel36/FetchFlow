# Tutorial: Price Comparison Across Multiple E-Commerce Stores

This tutorial demonstrates how to perform price comparisons across multiple e-commerce websites (such as **Delhaize** and **Colruyt**) using Jexflow as a Python library without writing website-specific scraping logic in Python.

By defining the site-specific extraction rules in configuration JSON files (such as `delhaize.json` and `colruyt.json`), an external developer can write a single, generic Python script that imports `Scraper` from `scraper_engine`, executes all workflow steps for each store, and aggregates the results for price comparison.

---

## 1. Overview & Goal

Imagine you want to compare the price of **Coca-Cola** between two Belgian supermarkets:
- **Delhaize**: `https://www.delhaize.be/shop/search?q=coca%20cola%3Arelevance&text=coca%20cola&sort=relevance`
- **Colruyt**: `https://www.colruyt.be/fr/produits?method=user%20typed&o=product%20overview&page=1&searchTerm=coca%20cola&suggestion=none&type=product`

Instead of writing custom BeautifulSoup or Selenium code for each website, you create a JSON configuration for each target site. Your Python application then imports the `Scraper` class from `scraper_engine` and executes them generically.

---

## 2. Installation & Module Setup

An external developer using Jexflow in their project will first add the package or project dependencies to `requirements.txt`:

```text
# requirements.txt
-e git+https://github.com/your-org/jexflow.git#egg=jexflow
```

Once installed via `pip install -r requirements.txt`, the engine module is imported in Python as `scraper_engine`:

```python
from scraper_engine import Scraper
```

---

## 3. Configuration Files

The JSON configuration files reside in the `examples/` directory.

### [`examples/delhaize.json`](../examples/delhaize.json)
```json
{
  "name": "delhaize_coca_cola_search",
  "version": "1.0",
  "variables": {
    "search_term": "coca cola"
  },
  "steps": [
    {
      "id": "products",
      "request": {
        "method": "GET",
        "url": "https://www.delhaize.be/shop/search?q={{search_term}}%3Arelevance&text={{search_term}}&sort=relevance"
      },
      "extract": {
        "selector": ".product-item, [data-testimonial='product-card']",
        "selector_type": "css"
      },
      "fields": {
        "title": {
          "selector": ".product-title, .product-name, h3",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim"
          ]
        },
        "price": {
          "selector": ".product-price, .price-amount",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim",
            {
              "regex": "([0-9]+[.,][0-9]{2})"
            }
          ]
        }
      }
    }
  ]
}
```

### [`examples/colruyt.json`](../examples/colruyt.json)
```json
{
  "name": "colruyt_coca_cola_search",
  "version": "1.0",
  "variables": {
    "search_term": "coca cola"
  },
  "steps": [
    {
      "id": "products",
      "request": {
        "method": "GET",
        "url": "https://www.colruyt.be/fr/produits?method=user%20typed&o=product%20overview&page=1&searchTerm={{search_term}}&suggestion=none&type=product"
      },
      "extract": {
        "selector": ".product-grid__item, .product-card",
        "selector_type": "css"
      },
      "fields": {
        "title": {
          "selector": ".product-card__title, .product-name, h3",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim"
          ]
        },
        "price": {
          "selector": ".product-card__price, .price-value",
          "selector_type": "css",
          "type": "text",
          "transform": [
            "trim",
            {
              "regex": "([0-9]+[.,][0-9]{2})"
            }
          ]
        }
      }
    }
  ]
}
```

---

## 4. Generic Python Execution Code (Using Jexflow as a Library)

Below is a complete example of how an external developer uses Jexflow programmatically in Python:

```python
from pathlib import Path
from scraper_engine import Scraper

def compare_prices(config_paths: list[str | Path]) -> dict[str, list[dict]]:
    """Generic price comparison function using Jexflow as a Python library.

    Args:
        config_paths: List of file paths to JSON configurations.

    Returns:
        A dictionary mapping store configuration name to extracted product items.
    """
    comparison_results = {}

    for config_path in config_paths:
        # Initialize Scraper directly with the JSON config file path
        scraper = Scraper(config_path)

        # Execute all workflow steps generically
        results = scraper.run()

        # Store results under the workflow name
        store_name = scraper.config.get("name", str(config_path))
        comparison_results[store_name] = results

    return comparison_results

if __name__ == "__main__":
    configs = [
        Path("examples/delhaize.json"),
        Path("examples/colruyt.json"),
    ]

    # Run price comparison for both stores
    all_prices = compare_prices(configs)

    # Display results
    for store, items in all_prices.items():
        print(f"\n=== {store} ===")
        for item in items:
            title = item.get("title", "Unknown Product")
            price = item.get("price", "N/A")
            print(f"- {title}: €{price}")
```

---

## 5. Key Takeaways

1. **Separation of Concerns**: HTML parsing rules and request URLs are defined entirely in JSON configurations ([`delhaize.json`](../examples/delhaize.json) and [`colruyt.json`](../examples/colruyt.json)), while Python code remains 100% generic.
2. **Scalability**: To add a new store (e.g., Carrefour or Albert Heijn), simply create a new JSON configuration file and add its path to `config_paths`. No Python code changes are required.
3. **Data Uniformity**: Transformation pipelines (such as `trim` and `regex`) standardize output fields so all stores yield consistent output keys and formatted numbers.
