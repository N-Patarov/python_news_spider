import scrapy
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from scrapy.selector import Selector
import cssutils
import csv

class ArticlesSpider(scrapy.Spider):
    
    name = "articles"

    crime_temp = []
    local_temp = []
    regional_temp = []

    #initialize browser
    browser = webdriver.Chrome("/usr/lib/chromium-browser/chromedriver")
    browser.maximize_window()
 
    start_urls = [
        "https://www.aspentimes.com/recent-stories/local/",
        "https://www.aspentimes.com/recent-stories/crime/",
        "https://www.aspentimes.com/recent-stories/regional/"
    ]

    # Saves data to csv file
    def save(self, temp_data, file_name):
        file = open(file_name, 'w', newline='')
        csv_writer = csv.writer(file)
        count = 0
        for data in temp_data:
            if count == 0:
                header = data.keys()
                csv_writer.writerow(header)
                count += 1
            csv_writer.writerow(data.values())
        
        file.close()

    def scrape_html(self, response):
        browser = self.browser
        page_source = browser.page_source       # Get the HTML of the page (STRING)
        html = Selector(text=page_source)       # Make string scrapeable
        articles = html.css('article.result').getall()
        for a in articles:
            article = Selector(text=a)  # Make string scrapeable

            # extract css from element
            div_style = article.css('div.briefs-img-container.align-items-center::attr(style)').get()
            style = cssutils.parseStyle(div_style)
            url = style['background-image']

            # url looks like this: url('https://www.aspentimes.com/wp-content/uploads/sites/5/2022/07/krabloonik-atd-070622-300x225.jpeg')
            # so i am just removing the brackets
            url = url.replace('url(', '').replace(')', '')
            
            json = {
                'title' : article.css('h5 *::text').get(),
                'date' : article.css('p.meta.briefs-datestamp *::text').get(),
                'description' : article.css('p.excerpt.d-block.d-sm-none.d-md-block *::text').get(),
                'article_link' : article.css('a::attr(href)').get(),
                'image_link' : url
            }
            # Save to array so i can save to csv
            if response.url == "https://www.aspentimes.com/recent-stories/local/":
                self.local_temp.append(json)
            elif response.url == "https://www.aspentimes.com/recent-stories/crime/":
                self.crime_temp.append(json)
            elif response.url == "https://www.aspentimes.com/recent-stories/regional/":
                self.regional_temp.append(json)
            else:
                print("ERROR")
        

    # Selenium code to get the html (The page is JavaScript, so it must be used)
    def parse(self, response):
        
        browser = self.browser
           
        browser.get(response.url)
        
        # Wait for the content of the page to load
        timeout = 3
        try:
            element_present = EC.presence_of_element_located((By.ID, 'briefs-results'))
            WebDriverWait(browser, timeout).until(element_present)
        
        except TimeoutException:
            print("Timed out")
        
        finally:

            self.scrape_html(response)

            # Check which array should it save to csv
            if response.url == "https://www.aspentimes.com/recent-stories/local/":
                self.save(self.local_temp, "local.csv")

            elif response.url == "https://www.aspentimes.com/recent-stories/crime/":
                self.save(self.crime_temp, "crime.csv")

            elif response.url == "https://www.aspentimes.com/recent-stories/regional/":
                self.save(self.regional_temp, "regional.csv") 
            
