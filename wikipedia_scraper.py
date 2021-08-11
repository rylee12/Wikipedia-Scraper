import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

from bs4 import BeautifulSoup
from collections import Counter
import requests
import argparse
import re

# Reference link: https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Layout#Body_sections

# body: paragraph, div, table
class WikipediaScraper:
	def __init__(self):
		# results hold word frequency, hyperlinks holds links in each section
		self.results = {}
		self.hyperlinks = {}

	# Main function that web scrapes the wikipedia url
	def scrape_url(self, url):
		all_words = []
		links = []
		title = ""
		body = False
		wiki_base_link = "https://en.wikipedia.org"

		# Scrape wikipedia page for html / data
		response = requests.get(url)
		soup = BeautifulSoup(response.content, 'html.parser')

		stop_words = set(stopwords.words("english"))

		# 3 cases:
		# 1) Internal wiki link
		# 2) Citation link (move to references section)
		# 3) All other cases
		for tag in soup.find("p").next_siblings:
			if (tag.name == "p" or tag.name == "div" or tag.name == "table") and body:
				# search for all hyperlinks in sub-section and parse them
				anchor_tags = tag.find_all("a", href=True)
				for anchor in anchor_tags:
					if anchor["href"][:5] == "/wiki":
						links.append(wiki_base_link + anchor["href"])
					elif anchor["href"][:5] == "#cite":
						links.append(url + anchor["href"])
					else:
						links.append(anchor["href"])

				self.filter_words(tag, stop_words, all_words)
			else:
				if tag.name == "h2":
					# Avoid empty list at start since we only want body sections
					if body:
						freq1 = Counter(all_words).most_common(10)
						self.results[title] = freq1
						self.hyperlinks[title] = links.copy()

					title = tag.get_text().strip()
					title = re.sub("([\(\[]).*?([\)\]])", "", title)
					body = True
					all_words.clear()
					links.clear()

	def filter_words(self, tag, stop_words, all_words):
		# Filter non-english characters and puncutations from string
		text_string = tag.get_text().strip().encode("ascii", "ignore").decode()
		text_string = re.sub("([\(\[]).*?([\)\]])", "", text_string)
		text_string = re.sub(r'[^\w\d\s\-\']+', '', text_string)

		words = [word for word in text_string.split() if word.lower() not in stop_words]
		all_words.extend(words)
	
	def print_results(self):
		results = self.results
		hyperlinks = self.hyperlinks
		for title in results:
			print("Title of Section: " + title)
			print()

			print("Most frequent words: ")
			for words in results[title]:
				print(words[0] + ": " + str(words[1]))
			print()

			print("Hyperlinks in " + title + ":")
			for links in hyperlinks[title]:
				print(links)
			print()


def load_scraper(url):
	scraper = WikipediaScraper()
	scraper.scrape_url(url)
	return scraper


# Only works for english wikipedia
if __name__=="__main__":
	parser = argparse.ArgumentParser(description ='Scrape frequent words and hyperlinks of Wikipedia url')
	parser.add_argument("url", metavar="url", type=str, help="Url to data scrape for")
	args = parser.parse_args()
	url = args.url

	assert(url[:24] == "https://en.wikipedia.org"), "Url is not a valid wikipedia url"

	scraper = load_scraper(url)
	scraper.print_results()
