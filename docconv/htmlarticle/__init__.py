import copy
import json
from datetime import datetime
import calendar
import regex
from urllib.parse import urljoin
from newspaper import Article as NewspaperArticle
from newspaper.cleaners import DocumentCleaner
import dateutil
from newspaper.outputformatters import OutputFormatter
from newspaper.videos.extractors import VideoExtractor

MAX_NUMBER_OF_WORDS_IN_AUTHOR = 10

IMAGE_URL_EXCLUSION_PATTERN = regex.compile(r".svg\s*$|placeholder|base64|icon|javascript", regex.IGNORECASE)
AUTHOR_KEYWORD_PATTERN_PART = r'(?:By|Author|Authors|Author\(s\)):'
AUTHOR_DIRECTLY_AFTER_KEYWORD_PATTERN = regex.compile(rf"{AUTHOR_KEYWORD_PATTERN_PART}\s*(.+?)\s*+$",
                                                      regex.MULTILINE)
STRIP_BY_FROM_AUTHOR_BEGINNING_PATTERN = regex.compile(r'^By\b', regex.IGNORECASE)
AUTHOR_WHITELIST_PATTERN = regex.compile(r"^\s*\p{Lu}[-.\p{L}]+\s+.*\b\p{Lu}[-.\p{L}]+(?:\s|$)")
AUTHOR_BLACKLIST_PATTERN = regex.compile(r"\b(the|society|center|centre|city|authors?|article|information|news|site|"
                                         r"community|gmbh|inc|guests?|staff|candidates?|"
                                         r"ltd|corp|executive|director|academic|faculty|university|colleges?|medicine|"
                                         r"medical|leadership|hospitals?|health|services?|computer|science|department|"
                                         r"editorial|editors?|board|faq|united|north|south|new|national|programs?|"
                                         r"subjects?|journals?|correspondence|google|facebook|www|scholar|scholarships?"
                                         r"|institutes?|quality|committees?|assistants?|members?)\b", regex.IGNORECASE)

PUBLISH_DATE_TAGS = [
            {'attribute': 'property', 'value': 'rnews:datePublished', 'content': 'content'},
            {'attribute': 'property', 'value': 'article:published_time', 'content': 'content'},
            {'attribute': 'name', 'value': 'OriginalPublicationDate', 'content': 'content'},
            {'attribute': 'itemprop', 'value': 'datePublished', 'content': 'datetime'},
            {'attribute': 'itemprop', 'value': 'datePublished', 'content': 'content'},
            {'attribute': 'property', 'value': 'og:published_time', 'content': 'content'},
            {'attribute': 'name', 'value': 'article_date_original', 'content': 'content'},
            {'attribute': 'name', 'value': 'publication_date', 'content': 'content'},
            {'attribute': 'name', 'value': 'publicationDate', 'content': 'content'},
            {'attribute': 'name', 'value': 'sailthru.date', 'content': 'content'},
            {'attribute': 'name', 'value': 'PublishDate', 'content': 'content'},
            {'attribute': 'pubdate', 'value': 'pubdate', 'content': 'datetime'},
            {'attribute': 'property', 'value': 'pubDate', 'content': 'content'}
]


class HtmlArticleExtractor:

    def __init__(self):
        pass

    def extract(self, html, source_url):
        if not html or not html.strip():
            return HtmlArticle("")
        newspaper_article = NewspaperArticle(source_url)
        newspaper_article.download(input_html=html)
        self.parse_for_relevant_attributes(newspaper_article)
        top_node = self.get_unmodified_top_node_from_original_html(newspaper_article)
        image_urls = []
        authors = []

        if top_node is not None:
            image_urls = self.extract_images_from_article(newspaper_article, top_node)
            authors = self.extract_author_by_keyword_from_article(top_node) \
                or self.extract_authors_by_keyword_above_article(top_node) \
                or self.extract_authors_from_a_with_author_class(top_node) \
                or self.extract_authors_from_li_or_span_with_author_class(top_node) \
                or self.extract_authors_from_a_with_author_class_above_article(top_node) \
                or self.extract_authors_from_li_or_span_with_author_class_above_article(top_node) \
                or self.extract_authors_from_div_with_author_class(top_node) \
                or self.extract_authors_from_div_with_author_class_above_article(top_node)

        return HtmlArticle(newspaper_article.text,
                           authors=self.unique_list(authors),
                           title=newspaper_article.title,
                           image_urls=image_urls,
                           publication_date=newspaper_article.publish_date[1]
                           if newspaper_article.publish_date else None,
                           publication_date_display=newspaper_article.publish_date[0]
                           if newspaper_article.publish_date else None)

    def parse_for_relevant_attributes(self, newspaper_article):
        newspaper_article.throw_if_not_downloaded_verbose()

        newspaper_article.doc = newspaper_article.config.get_parser().fromstring(newspaper_article.html)
        newspaper_article.clean_doc = copy.deepcopy(newspaper_article.doc)

        if newspaper_article.doc is None:
            return

        parse_candidate = newspaper_article.get_parse_candidate()
        newspaper_article.link_hash = parse_candidate.link_hash  # MD5

        document_cleaner = DocumentCleaner(newspaper_article.config)
        output_formatter = OutputFormatter(newspaper_article.config)

        title = newspaper_article.extractor.get_title(newspaper_article.clean_doc)
        newspaper_article.set_title(title)

        newspaper_article.publish_date = self.get_publish_date(newspaper_article)

        meta_lang = newspaper_article.extractor.get_meta_lang(newspaper_article.clean_doc)
        newspaper_article.set_meta_language(meta_lang)

        if newspaper_article.config.use_meta_language:
            newspaper_article.extractor.update_language(newspaper_article.meta_lang)
            output_formatter.update_language(newspaper_article.meta_lang)

        newspaper_article.doc = document_cleaner.clean(newspaper_article.doc)

        newspaper_article.top_node = newspaper_article.extractor.calculate_best_node(newspaper_article.doc)
        if newspaper_article.top_node is not None:
            video_extractor = VideoExtractor(newspaper_article.config, newspaper_article.top_node)
            newspaper_article.set_movies(video_extractor.get_videos())

            newspaper_article.top_node = newspaper_article.extractor.post_cleanup(newspaper_article.top_node)
            newspaper_article.clean_top_node = copy.deepcopy(newspaper_article.top_node)

            text, article_html = output_formatter.get_formatted(
                newspaper_article.top_node)
            newspaper_article.set_article_html(article_html)
            newspaper_article.set_text(text.strip())

        newspaper_article.is_parsed = True
        newspaper_article.release_resources()

    @staticmethod
    def get_unmodified_top_node_from_original_html(newspaper_article):
        # The clean_top_node is not so clean anymore (tag names are replaced by others, e.g. span -> p)
        modified_top_node = newspaper_article.clean_top_node
        if modified_top_node is None:
            return None
        top_node_classes = modified_top_node.attrib['class'] if 'class' in modified_top_node.attrib else None
        top_node_candidates_in_original_html = \
            newspaper_article.clean_doc.xpath(f"//{modified_top_node.tag}[@class='{top_node_classes}']") \
            if top_node_classes else newspaper_article.clean_doc.xpath(f"//{modified_top_node.tag}")
        unmodified_top_node = next(filter(lambda node: node.sourceline == modified_top_node.sourceline,
                                          top_node_candidates_in_original_html), None)
        return unmodified_top_node

    def extract_author_by_keyword_from_article(self, top_node, xpath_prefix="."):
        return self.look_for_authors_in_tags_following_a_span_containing_only_keyword(top_node, xpath_prefix) or \
               self.look_for_author_in_same_tag_that_starts_with_keyword(top_node, xpath_prefix)

    def extract_authors_by_keyword_above_article(self, top_node):
        return self.extract_author_by_keyword_from_article(top_node, './preceding::*')

    def extract_authors_from_a_with_author_class(self, top_node, xpath_prefix="."):
        links_with_author_class = top_node.xpath(f"{xpath_prefix}//a[contains(@class,'author') "
                                                 f"and not(contains(@class,'affiliation'))]")
        authors = []
        for link in links_with_author_class:
            text_within_link = link.xpath(".//text()")
            if text_within_link:
                text_to_extract_from =\
                    " ".join(text_part for text_part in text_within_link
                             if len(text_part.strip()) > 1 or text_part.strip() == ',')
                author_names = self.get_author_names(text_to_extract_from.strip())
                authors.extend(author_names)
        return authors

    def extract_authors_from_a_with_author_class_above_article(self, top_node):
        return self.extract_authors_from_a_with_author_class(top_node, './preceding::*')

    def extract_authors_from_li_or_span_with_author_class(self, top_node, xpath_prefix="."):
        texts_from_elements_with_author_class = top_node.xpath(f"{xpath_prefix}//*[self::li or self::span]"
                                                               f"[contains(@class,'author') "
                                                               f"and not(contains(@class,'affiliation'))]//text()")
        return self.extract_authors_from_text_parts(texts_from_elements_with_author_class)

    def extract_authors_from_li_or_span_with_author_class_above_article(self, top_node):
        return self.extract_authors_from_li_or_span_with_author_class(top_node, './preceding::*')

    def extract_authors_from_div_with_author_class(self, top_node, xpath_prefix='.'):
        texts_from_div_tags_with_author_class = top_node.xpath(f"{xpath_prefix}//div"
                                                               f"[contains(@class,'author') "
                                                               f"and not(contains(@class,'authors-info')) "
                                                               f"and not(contains(@class,'affiliation')) "
                                                               f"and not(contains(@class,'related'))]//text()")
        return self.extract_authors_from_text_parts(texts_from_div_tags_with_author_class)

    def extract_authors_from_div_with_author_class_above_article(self, top_node):
        return self.extract_authors_from_div_with_author_class(top_node, './preceding::*')

    def extract_authors_from_text_parts(self, texts_from_elements_with_author_class):
        authors = []
        for text in texts_from_elements_with_author_class:
            author_names = self.get_author_names(text.strip())
            authors.extend(author_names)
        return authors

    def look_for_authors_in_tags_following_a_span_containing_only_keyword(self, top_node, xpath_prefix="."):
        author_keyword_elements = top_node.xpath(f"{xpath_prefix}//span[normalize-space(text())='By:' "
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
            if len(keyword_element_following_siblings) < 1:
                return []
            element_after_keyword_element = keyword_element_following_siblings[0]
            if element_after_keyword_element.tag == 'dd':
                table_elements = element_after_keyword_element.xpath("./*")
                return self.extract_authors_from_elements(table_elements)
            elif element_after_keyword_element.tag == 'ul':
                list_elements = element_after_keyword_element.xpath("./li/*")
                return self.extract_authors_from_elements(list_elements)
            return self.extract_authors_from_elements(keyword_element_following_siblings, nested_extraction=False)

    def look_for_author_in_same_tag_that_starts_with_keyword(self, top_node, xpath_prefix="."):
        author_keyword_elements = top_node.xpath(f"{xpath_prefix}//*[starts-with(text(),'By:') "
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
        author_candidates = regex.split(r',|\band\b', text)
        for author_candidate in author_candidates:
            cleansed_author_candidate = regex.sub(STRIP_BY_FROM_AUTHOR_BEGINNING_PATTERN, '',
                                                  HtmlArticleExtractor.normalize_spaces(author_candidate)).strip()
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
        unique_image_urls = HtmlArticleExtractor.unique_list(image_urls)
        return unique_image_urls

    @staticmethod
    def image_source_is_valid(image_url):
        if not image_url:
            return False
        return not IMAGE_URL_EXCLUSION_PATTERN.search(image_url)

    @staticmethod
    def unique_list(authors):
        return list(dict.fromkeys(authors))

    def get_publish_date(self, newspaper_article):
        for known_meta_tag in PUBLISH_DATE_TAGS:
            meta_tags = newspaper_article.extractor.parser.getElementsByTag(
                newspaper_article.clean_doc,
                attr=known_meta_tag['attribute'],
                value=known_meta_tag['value'])
            if meta_tags:
                original_publish_date_str = newspaper_article.extractor.parser.getAttribute(
                    meta_tags[0],
                    known_meta_tag['content'])
                publish_date_from_meta = self.get_date_result(original_publish_date_str)
                if publish_date_from_meta:
                    return publish_date_from_meta

        ld_script_publication_date = newspaper_article.clean_doc.xpath("//script[@type='application/ld+json']")
        if ld_script_publication_date and len(ld_script_publication_date) > 0:
            try:
                ld_script_publish_date_str = json.loads(ld_script_publication_date[0].text)
                return self.get_date_result(ld_script_publish_date_str.get('datePublished', None))
            except:
                pass
        return None

    def get_date_result(self, original_publish_date_str):
        publish_date_time = self.parse_date(original_publish_date_str)
        if publish_date_time:
            return self.display_date(original_publish_date_str), publish_date_time

    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return None
        try:
            return dateutil.parser.parse(date_str, default=datetime(1970, 1, 1))
        except (ValueError, OverflowError, AttributeError, TypeError):
            return None

    @staticmethod
    def display_date(date_str):
        if not date_str:
            return None
        try:
            date_result = dateutil.parser.DEFAULTPARSER._parse(date_str)[0]
            year = date_result.year if date_result.year else ""
            month = calendar.month_name[date_result.month] if date_result.month else ""
            day = f" {str(date_result.day).zfill(2)}" if date_result.day else ""
            return f"{month}{day}, {year}".strip(", ")
        except (ValueError, OverflowError, AttributeError, TypeError):
            return None


class HtmlArticle:

    def __init__(self, text, title='', authors=[], publication_date=None, publication_date_display=None, image_urls=[]):
        self.text = text
        self.authors = authors
        self.image_urls = image_urls
        self.publication_date = publication_date
        self.publication_date_display = publication_date_display
        self.title = title

