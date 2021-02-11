from bs4 import BeautifulSoup
from bs4.element import PreformattedString, NavigableString


class Html2TextChunksConverter:

    @staticmethod
    def to_text_chunks(html_content):
        parser = ChunkHTMLParser()
        parser.parse(html_content)
        return parser.chunks


class ArticleDetector:

    def __init__(self,  min_article_length=1000, min_chunk_length=50):
        self.min_article_length = min_article_length
        self.min_chunk_length = min_chunk_length

    def is_article(self, chunks):
        num_of_characters_in_valid_chunks = sum(len(chunk.data) for chunk in chunks
                                                if len(chunk.data) >= self.min_chunk_length)
        return num_of_characters_in_valid_chunks >= self.min_article_length


class ArticleChunksExtractor:

    def __init__(self, min_text_paragraph_length=200):
        self.min_text_paragraph_length = min_text_paragraph_length

    def extract(self, chunks):
        try:
            index, _ = next((idx, chunk) for idx, chunk in enumerate(chunks)
                            if len(chunk.data) >= self.min_text_paragraph_length)
        except StopIteration:
            return chunks
        headline_idx = index
        for i in self.get_range_for_five_preceeding_elements(index):
            if chunks[i].chunk_type == Chunk.headline_type:
                headline_idx = i
        return chunks[headline_idx:]

    @staticmethod
    def get_range_for_five_preceeding_elements(index):
        return range(index, max(-1, index - 6), -1)


class HTMLParser(object):

    def __init__(self):
        pass

    def parse(self, html_input):
        body = None
        if is_not_blank(html_input):
            body = self.__get_cleansed_html_body(html_input)
        return body

    def to_text(self, html_input, text_separator="\n"):
        if is_blank(html_input):
            return None
        soup = self._get_clean_soup(html_input)
        return soup.getText(separator=text_separator)

    def __get_cleansed_html_body(self, html_input):
        soup = self._get_clean_soup(html_input)
        return soup.body

    def _get_clean_soup(self, html_input):
        soup = BeautifulSoup(html_input, "html.parser")
        declarations_and_comments = soup.findAll(text=lambda text: isinstance(text, PreformattedString))
        self.delete_subtree(declarations_and_comments)
        self.__find_and_delete_sub_tree(soup, 'script')
        self.__find_and_delete_sub_tree(soup, 'style')
        return soup

    def __find_and_delete_sub_tree(self, soup, tag_name, attr={}):
        script_elements = soup.findAll(tag_name, attr)
        self.delete_subtree(script_elements)

    @staticmethod
    def delete_subtree(comments):
        [x.extract() for x in comments]


class ChunkHTMLParser(HTMLParser):

    FLOW_PRESERVING_TAG = ['span', 'sub', 'sup', 'abbr', 'acronym', 'em', 'b', 'font', 'i', 'strong', 'u', 'a']

    def __init__(self, min_chunk_length=-1):
        super(ChunkHTMLParser, self).__init__()
        self.min_chunk_length = min_chunk_length
        self.chunks = []

    def parse(self, html_input):
        body = super(ChunkHTMLParser, self).parse(html_input)
        self.chunks = []
        self.current_chunk = None
        self.current_chunk_type = None

        if not body:
            return

        self.__traverse(body)
        self.__save_current_chunk_if_valid()

    def __save_current_chunk_if_valid(self):
        # not correct; counts space added in handleText too
        if self.current_chunk is not None and len(self.current_chunk.data) >= self.min_chunk_length:
            self.chunks.append(self.current_chunk)
        self.current_chunk = None

    def __traverse(self, elements):
        for element in elements:
            if isinstance(element, NavigableString):
                self.__handle_text(element)
            else:
                self.__set_current_chunk_type(element)
                was_flow_breaking_tag = self.__handle_tag(element)
                self.__traverse(element.contents)
                if was_flow_breaking_tag:
                    self.__save_current_chunk_if_valid()

    def __set_current_chunk_type(self, element):
        if element.name not in self.FLOW_PRESERVING_TAG:
            self.current_chunk_type = self.__get_element_type(element.name)

    @staticmethod
    def __get_element_type(tag_name):
        current_element_type = None
        if tag_name == 'li':
            current_element_type = Chunk.list_type
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            current_element_type = Chunk.headline_type
        return current_element_type

    def __handle_text(self, text):
        if is_not_blank(text):
            text = text.strip()
            if self.current_chunk is None:
                self.current_chunk = Chunk(text, self.current_chunk_type)
                self.current_chunk_type = None
            else:
                self.current_chunk.add_data(text)

    def __handle_tag(self, tag): #TODO: what about one p after another closing p?
        # TODO: https://developer.mozilla.org/de/docs/Web/HTML/Inline_elements
        if tag.name not in self.FLOW_PRESERVING_TAG:
            self.__save_current_chunk_if_valid()
            return True
        return False

    def chunks_as_text(self):
        if self.chunks:
            return "\n".join([chunk.data for chunk in self.chunks])
        return ""


class Chunk:

    headline_type = 'headline'
    list_type = 'list'

    def __init__(self, data, chunk_type=None):
        self.data = data
        self.chunk_type = chunk_type

    def add_data(self, data):
        self.data = "%s %s" % (self.data, data)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)


def is_blank(input_string):
    return input_string is None or input_string.strip() == ""


def is_not_blank(input_string):
    return not is_blank(input_string)
