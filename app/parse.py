import csv
from urllib.parse import urljoin

import requests
import os
from dataclasses import dataclass

from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Quote:
    text: str
    author: str
    tags: list[str]


@dataclass
class Bio:
    title: str
    description: str


def parse_single_bio(bio_soup: BeautifulSoup) -> Bio:
    return Bio(
        title=bio_soup.select_one(".author-title").text,
        description=bio_soup.select_one(".author-description").text,
    )


def parse_single_quote(
    quote_soup: BeautifulSoup, href_vals: list[str]
) -> Quote:
    anchor_tag = quote_soup.select_one(".author + a")
    if anchor_tag is not None:
        href_value = anchor_tag.get("href")
        if href_value not in href_vals:
            href_vals.append(href_value)

    return Quote(
        text=quote_soup.select_one(".text").text,
        author=quote_soup.select_one(".author").text,
        tags=[tag.text for tag in quote_soup.select(".tag")],
    )


def get_single_page_quotes(
    quote_soup: BeautifulSoup, href_vals: list[str]
) -> list[Quote]:
    quotes = quote_soup.select(".quote")
    return [parse_single_quote(quote, href_vals) for quote in quotes]


def get_quotes() -> tuple[list[Quote], list[Bio]]:
    href_vals = []

    base_url = os.environ.get("BASE_URL")

    page = requests.get(base_url).content
    first_page_soup = BeautifulSoup(page, "html.parser")
    all_quotes = get_single_page_quotes(first_page_soup, href_vals)

    i = 2
    while True:
        next_page = urljoin(base_url, f"/page/{i}")
        next_page_url = requests.get(next_page).content
        next_page_soup = BeautifulSoup(next_page_url, "html.parser")

        quotes_on_page = get_single_page_quotes(next_page_soup, href_vals)

        if not quotes_on_page:
            break

        all_quotes.extend(quotes_on_page)
        i += 1

    bios_list = []

    for author_url in href_vals:
        bio_page = urljoin(base_url, author_url)
        bio_page_url = requests.get(bio_page).content
        bio_page_soup = BeautifulSoup(bio_page_url, "html.parser")
        author_details = bio_page_soup.select_one(".author-details")

        if author_details:
            res = parse_single_bio(author_details)
            bios_list.append(res)

    return all_quotes, bios_list


def write_bio_to_csv(bio_csv_path: str) -> None:
    with open(bio_csv_path, "w", encoding="utf-8", newline="") as bio_file:
        writer = csv.writer(bio_file, delimiter=";")

        writer.writerow(Bio.__annotations__.keys())
        _, bios = get_quotes()

        for bio in bios:
            title = bio.title
            description = bio.description.strip()
            writer.writerow([title, description])


def main(output_csv_path: str) -> None:
    with open(output_csv_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)

        writer.writerow(Quote.__annotations__.keys())
        quotes, _ = get_quotes()

        for quote in quotes:
            text = quote.text
            author = quote.author
            tags = quote.tags
            writer.writerow([text, author, tags])


if __name__ == "__main__":
    write_bio_to_csv("bios.csv")
    main("quotes.csv")
