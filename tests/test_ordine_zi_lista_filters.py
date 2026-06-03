"""Playwright tests for ordine-zi-lista.html filter behavior."""

import pytest
from playwright.sync_api import sync_playwright


BASE_URL = "http://localhost:8000/web/ordine-zi-lista.html?leg=2024"
TIMEOUT = 10000


@pytest.fixture
def browser():
    """Playwright browser fixture."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser):
    """Playwright page fixture."""
    page = browser.new_page()
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle", timeout=TIMEOUT)
    # Wait for data to load (results count to appear)
    page.wait_for_selector("#results-count", timeout=TIMEOUT)
    yield page
    page.close()


def get_result_count(page):
    """Extract the number of results from the results count text."""
    text = page.text_content("#results-count")
    # Format: "N puncte"
    return int(text.split()[0])


def test_no_filters_shows_all_items(page):
    """Baseline: no filters should show all items."""
    count = get_result_count(page)
    assert count > 0, "Should show items with no filters"
    print(f"✓ No filters: {count} items")


def test_single_item_type_filter(page):
    """Selecting item_type should narrow results."""
    initial_count = get_result_count(page)

    # Click "Proiecte lege" button
    page.click("button[data-type='bills']")
    page.wait_for_timeout(500)  # Wait for filter to apply

    bills_count = get_result_count(page)
    assert bills_count < initial_count, f"Bills ({bills_count}) should be < all items ({initial_count})"
    print(f"✓ Item type filter works: all={initial_count}, bills={bills_count}")


def test_single_commission_filter(page):
    """Selecting a commission should narrow results."""
    initial_count = get_result_count(page)

    # Click "juridica" commission checkbox
    page.click("label:has-text('juridica')")
    page.wait_for_timeout(500)

    juridica_count = get_result_count(page)
    assert juridica_count <= initial_count, f"Juridica ({juridica_count}) should be <= all ({initial_count})"
    print(f"✓ Commission filter works: all={initial_count}, juridica={juridica_count}")


def test_multiple_commissions_or_logic(page):
    """Selecting multiple commissions should use OR (expand results)."""
    # Select first commission
    page.click("label:has-text('juridica')")
    page.wait_for_timeout(300)
    count_1 = get_result_count(page)

    # Select second commission
    page.click("label:has-text('buget')")
    page.wait_for_timeout(300)
    count_2 = get_result_count(page)

    # Multiple commissions should show same or more items (OR logic)
    assert count_2 >= count_1, f"Multiple commissions ({count_2}) should be >= single ({count_1})"
    print(f"✓ Multiple commissions use OR: juridica={count_1}, juridica+buget={count_2}")


def test_multiple_dimensions_and_logic(page):
    """Selecting filters from different dimensions should use AND (narrow results)."""
    # Select item_type
    page.click("button[data-type='bills']")
    page.wait_for_timeout(300)
    count_1 = get_result_count(page)

    # Add commission filter
    page.click("label:has-text('juridica')")
    page.wait_for_timeout(300)
    count_2 = get_result_count(page)

    # Adding filter from different dimension should narrow
    assert count_2 <= count_1, f"Bills+juridica ({count_2}) should be <= bills ({count_1})"
    print(f"✓ Multiple dimensions use AND: bills={count_1}, bills+juridica={count_2}")


def test_flag_filters(page):
    """Flag filters should narrow results (AND within dimension)."""
    initial_count = get_result_count(page)

    # Click "urgență" flag
    page.click("label:has-text('urgență')")
    page.wait_for_timeout(300)
    urgent_count = get_result_count(page)

    assert urgent_count <= initial_count, f"Urgent ({urgent_count}) should be <= all ({initial_count})"
    print(f"✓ Flag filter works: all={initial_count}, urgent={urgent_count}")


def test_act_type_filters_or_logic(page):
    """Act type filters should use OR (expand results)."""
    # Select first act type
    page.click("label:has-text('CCR'):nth-of-type(2)")  # Act types, not commissions
    page.wait_for_timeout(300)
    count_1 = get_result_count(page)

    # Select second act type
    page.click("label:has-text('Lege')")
    page.wait_for_timeout(300)
    count_2 = get_result_count(page)

    # Multiple act types should show same or more items (OR logic)
    assert count_2 >= count_1, f"Multiple acts ({count_2}) should be >= single ({count_1})"
    print(f"✓ Act types use OR: CCR={count_1}, CCR+Lege={count_2}")


def test_text_search_narrows(page):
    """Text search should narrow results."""
    initial_count = get_result_count(page)

    # Type search term
    page.fill("input[placeholder*='căutare']", "cod penal")
    page.wait_for_timeout(500)  # Debounce delay

    search_count = get_result_count(page)
    assert search_count <= initial_count, f"Search ({search_count}) should be <= all ({initial_count})"
    print(f"✓ Text search works: all={initial_count}, 'cod penal'={search_count}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
