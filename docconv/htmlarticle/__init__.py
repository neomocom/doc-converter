import regex
from urllib.parse import urljoin

from newspaper import Article as NewspaperArticle
from newspaper.configuration import Configuration

MAX_NUMBER_OF_WORDS_IN_AUTHOR = 10

IMAGE_URL_EXCLUSION_PATTERN = regex.compile(r".svg\s*$|placeholder|base64|javascript", regex.IGNORECASE)
AUTHOR_KEYWORD_PATTERN_PART = r'(?:By|Author|Authors|Author\(s\)):'
AUTHOR_DIRECTLY_AFTER_KEYWORD_PATTERN = regex.compile(rf"{AUTHOR_KEYWORD_PATTERN_PART}\s*(.+?)\s*+$",
                                                      regex.MULTILINE)
AUTHOR_WHITELIST_PATTERN = regex.compile(r"^\s*\p{Lu}[-.\p{L}]+\s+.*\b\p{Lu}[-.\p{L}]+(?:\s|$)")
AUTHOR_BLACKLIST_PATTERN = regex.compile(r"\b(society|center|city|authors?|news|community|gmbh|inc|ltd|corp)\b",
                                         regex.IGNORECASE)


class HtmlArticleExtractor:

    def __init__(self):
        self.config = Configuration()
        self.config.fetch_images = False

    def extract(self, html, source_url):
        if not html or not html.strip():
            return HtmlArticle("")
        newspaper_article = NewspaperArticle(source_url, config=self.config)
        newspaper_article.download(input_html=html)
        newspaper_article.parse()
        top_node = self.get_unmodified_top_node_from_original_html(newspaper_article)
        image_urls = []
        authors = []

        if top_node:
            image_urls = self.extract_images_from_article(newspaper_article, top_node)
            authors = self.extract_author_from_article(top_node) \
                or self.extract_authors_from_elements_above_top_node(top_node)

        return HtmlArticle(newspaper_article.text,
                           authors=authors,
                           title=newspaper_article.title,
                           image_urls=image_urls)

    def extract_authors_from_elements_above_top_node(self, top_node):
        author_containers_preceding_top_node = \
            top_node.xpath("./preceding-sibling::*[contains(@class,'author')]")
        return self.extract_author_from_article(author_containers_preceding_top_node[0]) \
            if len(author_containers_preceding_top_node) > 0 else []

    @staticmethod
    def get_unmodified_top_node_from_original_html(newspaper_article):
        # The clean_top_node is not so clean anymore (tag names are replaced by others, e.g. span -> p)
        modified_top_node = newspaper_article.clean_top_node
        if not modified_top_node:
            return None
        top_node_classes = modified_top_node.attrib['class'] if 'class' in modified_top_node.attrib else None
        top_node_candidates_in_original_html = \
            newspaper_article.clean_doc.xpath(f"//{modified_top_node.tag}[@class='{top_node_classes}']") \
            if top_node_classes else newspaper_article.clean_doc.xpath(f"//{modified_top_node.tag}")
        unmodified_top_node = next(filter(lambda node: node.sourceline == modified_top_node.sourceline,
                                          top_node_candidates_in_original_html), None)
        return unmodified_top_node

    def extract_author_from_article(self, top_node):
        return self.look_for_authors_in_tags_following_a_span_containing_only_keyword(top_node) or \
               self.look_for_author_in_same_tag_that_starts_with_keyword(top_node)

    def look_for_authors_in_tags_following_a_span_containing_only_keyword(self, top_node):
        author_keyword_elements = top_node.xpath(".//span[normalize-space(text())='By:' "
                                                 "or normalize-space(text())='By' "
                                                 "or normalize-space(text())='Author:' "
                                                 "or normalize-space(text())='Author' "
                                                 "or normalize-space(text())='Authors:' "
                                                 "or normalize-space(text())='Authors' "
                                                 "or normalize-space(text())='Author(s):' "
                                                 "or normalize-space(text())='Author(s)']")
        if len(author_keyword_elements) > 0:
            first_author_keyword_element = author_keyword_elements[0]
            keyword_element_following_siblings = first_author_keyword_element.xpath("./following-sibling::*")
            if len(keyword_element_following_siblings) <= 0:
                return []
            element_after_keyword_element = keyword_element_following_siblings[0]
            if element_after_keyword_element.tag == 'dd':
                table_elements = element_after_keyword_element.xpath("./*")
                return self.extract_authors_from_elements(table_elements)
            elif element_after_keyword_element.tag == 'ul':
                list_elements = element_after_keyword_element.xpath("./li/*")
                return self.extract_authors_from_elements(list_elements)
            return self.extract_authors_from_elements(keyword_element_following_siblings, nested_extraction=False)

    def look_for_author_in_same_tag_that_starts_with_keyword(self, top_node):
        author_keyword_elements = top_node.xpath(".//*[starts-with(text(),'By:') "
                                                 "or starts-with(text(),'Author:') "
                                                 "or starts-with(text(),'Authors:') "
                                                 "or starts-with(text(),'Author(s):')]")
        if len(author_keyword_elements) > 0:
            author_keyword_element = author_keyword_elements[0]
            keyword_text = author_keyword_element.text.replace("\r", " ").replace("\n", " ")
            keyword_and_author_same_tag_match = AUTHOR_DIRECTLY_AFTER_KEYWORD_PATTERN.match(keyword_text)
            if keyword_and_author_same_tag_match:
                author_candidate = keyword_and_author_same_tag_match.group(1)
                return self.get_author_names(author_candidate)
        return []

    def extract_authors_from_elements(self, keyword_element_following_siblings, nested_extraction=True):
        authors = []
        for following_sibling in keyword_element_following_siblings:
            text = self.get_text_from_parent_and_child_nodes(following_sibling)\
                if nested_extraction else following_sibling.text
            if text and text.strip():
                author_names = self.get_author_names(text.strip())
                authors.extend(author_names)
        return authors

    @staticmethod
    def get_text_from_parent_and_child_nodes(following_sibling):
        return " ".join(following_sibling.xpath('.//text()'))

    @staticmethod
    def get_author_names(text):
        if not text:
            return []
        author_names = []
        author_candidates = text.split(',')
        for author_candidate in author_candidates:
            cleansed_author_candidate = HtmlArticleExtractor.normalize_spaces(author_candidate)
            if len(cleansed_author_candidate.split()) <= MAX_NUMBER_OF_WORDS_IN_AUTHOR \
                    and AUTHOR_WHITELIST_PATTERN.match(cleansed_author_candidate)\
                    and not AUTHOR_BLACKLIST_PATTERN.search(cleansed_author_candidate):
                author_names.append(cleansed_author_candidate)
        return author_names

    @staticmethod
    def normalize_spaces(text):
        return " ".join(text.split())

    @staticmethod
    def extract_images_from_article(newspaper_article, top_node):
        image_tags = newspaper_article.extractor.parser.getElementsByTag(top_node,
                                                                         **{'tag': 'img'})
        image_urls = [urljoin(newspaper_article.url, image_tag.get('src')) for image_tag in image_tags
                      if HtmlArticleExtractor.image_source_is_valid(image_tag.get('src'))]
        unique_image_urls = list(dict.fromkeys(image_urls))
        return unique_image_urls

    @staticmethod
    def image_source_is_valid(image_url):
        if not image_url:
            return False
        return not IMAGE_URL_EXCLUSION_PATTERN.search(image_url)


class HtmlArticle:

    def __init__(self, text, title='', authors=[], publish_date=None, image_urls=[]):
        self.text = text
        self.authors = authors
        self.image_urls = image_urls
        self.publish_date = publish_date
        self.title = title
