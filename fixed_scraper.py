from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.chrome.options import Options
import time
from bs4 import BeautifulSoup

def scrape_le360(max_articles=50):
    # Set up Selenium WebDriver (using Chrome in this example)
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--log-level=3")  # Suppress logs for cleaner output
    # Disable notifications to prevent OneSignal dialog
    chrome_options.add_argument("--disable-notifications")
    # Add preferences to block OneSignal popups
    prefs = {
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=chrome_options)

    driver.get("https://fr.le360.ma/")

    articles = []
    try:
        # First try to close any popup/overlay that might be present
        try:
            # Wait a bit for the page to load
            time.sleep(2)
            # Try to find and remove the OneSignal dialog
            driver.execute_script("""
                var element = document.getElementById('onesignal-slidedown-dialog');
                if(element) element.remove();
                var overlays = document.querySelectorAll('.onesignal-slidedown-dialog');
                overlays.forEach(function(overlay) {
                    overlay.remove();
                });
            """)
        except:
            pass
            
        while len(articles) < max_articles:
            # Find all article elements
            article_elements = driver.find_elements(By.CSS_SELECTOR, '.article-list-item')
            for article in article_elements[len(articles):]:  # Only process new articles
                try:
                    html = article.get_attribute("outerHTML")
                    soup = BeautifulSoup(html, "html.parser")
                    link = soup.find("div", class_="article-list--headline-container").find("a", recursive=False)["href"]
                    link = 'https://fr.le360.ma' + link
                    articles.append(link)
                    if len(articles) >= max_articles:
                        break
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
            
            if len(articles) >= max_articles:
                break
                
            # Click the "Afficher plus" button with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Remove any overlays before clicking
                    driver.execute_script("""
                        var element = document.getElementById('onesignal-slidedown-dialog');
                        if(element) element.remove();
                        var overlays = document.querySelectorAll('.onesignal-slidedown-dialog');
                        overlays.forEach(function(overlay) {
                            overlay.remove();
                        });
                    """)
                    
                    load_more = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '.results-list-load-more'))
                    )
                    
                    # Try JavaScript click instead of Selenium click
                    driver.execute_script("arguments[0].click();", load_more)
                    time.sleep(2)  # Wait for content to load
                    break  # If successful, break the retry loop
                except (TimeoutException, NoSuchElementException) as e:
                    print("No more articles to load or button not found")
                    break
                except ElementClickInterceptedException as e:
                    if attempt < max_retries - 1:
                        print(f"Click intercepted, retrying... Attempt {attempt+1}/{max_retries}")
                        time.sleep(1)  # Wait a bit before retrying
                    else:
                        print("Failed to click the load more button after multiple attempts")
                        break
    finally:
        driver.quit()

    return articles[:max_articles]

# The rest of your code remains the same
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def scrape_single_page(url):
    # Set up Selenium WebDriver with headless mode for faster execution
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")  # Disable GPU for headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--log-level=3")  # Suppress logs for cleaner output
    # Disable notifications to prevent OneSignal dialog
    chrome_options.add_argument("--disable-notifications")
    # Add preferences to block OneSignal popups
    prefs = {
        "profile.default_content_setting_values.notifications": 2
    }
    chrome_options.add_experimental_option("prefs", prefs)

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        
        # Locate the desired elements
        wait = WebDriverWait(driver, 5)  # Wait up to 5 seconds
        div_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.layout-section')))
        soup = BeautifulSoup(div_element.get_attribute('outerHTML'), 'html.parser')
        title = soup.find('h1').text.strip()
        link = url
        category = soup.find('a', class_='overline-link').text.strip()
        date = soup.find('div', class_='subheadline-date').text.strip()
        author_div = soup.find('div', class_='byline-credits')
        try:
            authors = [a.text.strip() for a in author_div.find_all('a')]
            author = ', '.join(authors) 
            if len(authors) == 0:
                authors = [s.text.strip() for s in author_div.find_all('span')]
                author = ', '.join(authors) if authors else "No author found"
        except AttributeError:
            author = "No author found"

        image = soup.find('div', class_='custom-image-wrapper --loaded').find('img')['src']
        description = soup.find('h2', class_='subheadline-container').text.strip()
        paragraphes_container = soup.find('article', class_='default__ArticleBody-sc-10mj2vp-2 NypNt article-body-wrapper')
        content = ''
        for p in paragraphes_container.find_all('p'):
            class_list = p.get('class', [])
            if set(['default__StyledText-sc-10mj2vp-0', 'fSEbof', 'body-paragraph']).issubset(class_list):
                content += '\n ' + p.text.strip()
            else:
                break
        article = {
            'title': title,
            'link': link,
            'category': category,
            'date': date,
            'description': description,
            'content': content,
            'image': image,
            'author': author
        }
        return article  # Return the article data
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None
    finally:
        driver.quit()  # Ensure the driver quits after execution

def process_articles(batch_size=5, max_articles=50):
    # Step 1: Get all article links
    try:
        all_links = scrape_le360(max_articles=max_articles)
        if len(all_links) == 0 or len(all_links) < max_articles:
            print(f"Warning: Found only {len(all_links)} articles, fewer than requested {max_articles}.")
        else:
            print(f"Found {len(all_links)} articles.")
    except Exception as e:
        print(f"Error scraping articles: {e}")
        return []

    # Step 2: Split links into sublists of batch_size
    chunks = [all_links[i:i + batch_size] for i in range(0, len(all_links), batch_size)]

    # Step 3: Process each chunk with ThreadPoolExecutor and accumulate results
    all_results = []
    for index, chunk in enumerate(chunks):
        try:
            with ThreadPoolExecutor(max_workers=len(chunk)) as executor:
                results = list(executor.map(scrape_single_page, chunk))
                # Filter out None results if any
                valid_results = [result for result in results if result is not None]
                if len(valid_results) == 0:
                    print(f"Error while scraping chunk number {index}, no results found")
                    continue
                else:
                    print(f"Processed chunk number {index} with {len(valid_results)} results.")
                all_results.extend(valid_results)  # Accumulate results
        except Exception as e:
            print(f"Error processing chunk number {index}: {e}")
            print(f"Chunk: {chunk}")
            continue
    return all_results

# Main execution
if __name__ == "__main__":
    data = process_articles(batch_size=5, max_articles=250)
    
    import pandas as pd
    if not data:
        print("No data to save.")
    else:
        df = pd.DataFrame(data)  # Convert list of dicts to DataFrame
        df.to_csv('le360_articles.csv', index=False, encoding='utf-8')  # Save as CSV without row numbers
        print(f"Saved {len(data)} articles to le360_articles.csv")
