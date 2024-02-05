from playwright.async_api import async_playwright
from asyncio import get_event_loop
import urllib.parse

query = "fashion"
encoded_query = urllib.parse.quote(query)

url = f"https://www.pinterest.com/search/pins/?q={encoded_query}"
search_results = []
image_results = []

async def scrape_pinterest_image(page):
    await page.wait_for_load_state('load')
    try:
        await page.wait_for_selector('div[data-test-id="CloseupMainPin"]',
                                     timeout=100000)

        await page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Selector did not appear: {e}")
        return image_results

    print("Selector found!")
    tags=[]
    images = await page.query_selector_all('img')
    titles = await page.query_selector_all('div[data-test-id="pinTitle"]')
    descriptions = await page.query_selector_all('div[data-test-id="truncated-description"]')
    user_logos = await page.query_selector_all('div[data-test-id="gestalt-avatar-svg"]')
    user_links = await page.query_selector_all('div[data-test-id="official-user-attribution"]')
    user_names = await page.query_selector_all('div[data-test-id="creator-profile-name"]')
    tag= await page.query_selector_all('div[data-test-id="vase-tag"]')

    image_url = await images[0].get_attribute('src') if images else None
    title_element = await titles[0].query_selector('h1') if titles else None
    title = await title_element.evaluate('(element) => element.textContent', title_element) if title_element else None
    description_element = await descriptions[0].query_selector('span') if descriptions else None
    description = await description_element.evaluate('(element) => element.textContent', description_element) if description_element else None
    user_logo_element = await user_logos[0].query_selector('img') if user_logos else None
    user_logo = await user_logo_element.get_attribute('src') if user_logo_element else None
    user_link_element = await user_links[0].query_selector('a') if user_links else None
    user_link = await user_link_element.get_attribute('href') if user_link_element else None
    user_name_element = await user_names[0].query_selector('.tBJ') if user_names else None
    user_name = await user_name_element.evaluate('(element) => element.textContent', user_name_element) if user_name_element else None
    for i in tag:
        tag_element = await i.query_selector('.Wk9') if i else None
        tagg= await tag_element.evaluate('(element) => element.textContent', tag_element) if tag_element else None
        tags.append(tagg)

    image_results.append({
        "image_url": image_url,
        "title": title,
        "description": description,
        "userLogo": user_logo,
        "userLink": user_link,
        "userName": user_name,
        "tags": tags

    })
    print(image_results)
    return image_results

async def scrape_pinterest_results(page):
    await page.wait_for_load_state('load')
    print("Waiting for selector to appear...")
    try:
        await page.wait_for_selector('div[data-test-id="masonry-container"]', timeout=100000)  # Adjust timeout as needed
        await page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Selector did not appear: {e}")
        return search_results
    print("Selector found!")
    results = await page.query_selector_all('.Yl-')
    for result in results:
        link_element = await result.query_selector('a')
        link = await link_element.get_attribute('href') if link_element else None
        search_results.append({
            'link': link,
        })
    print(search_results)
    return search_results


more_results = []


async def scrape_more_pinterest_results(page ):
    await page.wait_for_load_state('load')
    print("Waiting for selector to appear...")

    try:
        await page.wait_for_selector('div[data-test-id="masonry-container"]', timeout=100000)  # Adjust timeout as needed
        await page.wait_for_load_state('networkidle')
    except Exception as e:
        print(f"Selector did not appear: {e}")
        return more_results
    print("Selector found!")
    results = await page.query_selector_all('.Yl-')
    for result in results:
        link_element = await result.query_selector('a')
        link = await link_element.get_attribute('href') if link_element else None
        more_results.append({
            'link': link,
        })
    # print(more_results)
    return more_results


async def scroll_to_end(page):
    for _ in range(1):  # Adjust the range as needed

        await page.eval_on_selector("body", "body => window.scrollTo(0, body.scrollHeight)")
        results = await scrape_pinterest_results(page)
        await page.wait_for_timeout(1000)


async def more_like_this_scroll(page, search_results):
    results = []
    for _ in range(1):
        await page.eval_on_selector("body", "body => window.scrollTo(0, body.scrollHeight)")
        results = await scrape_more_pinterest_results(page)
        await page.wait_for_timeout(1000)
    search_results.extend(results)


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto(url)

        await page.wait_for_load_state('networkidle')

        await scroll_to_end(page)

        for result in search_results:
            link = result.get('link')
            nested_links = []
            more_results.clear()
            if link:
                await page.goto(f"https://www.pinterest.com{link}")
                image_result = await scrape_pinterest_image(page)
                await more_like_this_scroll(page,nested_links)
                result['more_like_this'] = nested_links
                await page.screenshot(path=f'./result_{link.replace("/", "_")}.png', full_page=True)

        print("search results", search_results)
        print("images", image_results)

        await page.screenshot(path='./pinterest_example.png', full_page=True)

        await browser.close()

if __name__ == "__main__":
    loop = get_event_loop()
    loop.run_until_complete(main())
