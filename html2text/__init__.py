from bs4 import BeautifulSoup
from bs4.element import PreformattedString, NavigableString


class Html2TextChunksConverter:

    @staticmethod
    def to_text_chunks(html_content):
        parser = ChunkHTMLParser()
        parser.parse(html_content)
        return parser.chunks


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

    def __init__(self, min_chunk_length=-1):
        super(ChunkHTMLParser, self).__init__()
        self.min_chunk_length = min_chunk_length
        self.chunks = []

    def parse(self, html_input):
        body = super(ChunkHTMLParser, self).parse(html_input)
        self.chunks = []
        self.current_chunk = None

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
                was_flow_breaking_tag = self.__handle_tag(element)
                self.__traverse(element.contents)
                if was_flow_breaking_tag:
                    self.__save_current_chunk_if_valid()

    def __handle_text(self, text):
        if is_not_blank(text):
            text = text.strip()
            if self.current_chunk is None:
                self.current_chunk = Chunk(text)
            else:
                self.current_chunk.add_data(text)

    def __handle_tag(self, tag): #TODO: what about one p after another closing p?
        # TODO: https://developer.mozilla.org/de/docs/Web/HTML/Inline_elemente
        if tag.name not in ['span', 'sub', 'sup', 'abbr', 'acronym', 'em', 'b', 'font', 'i', 'strong', 'u', 'a']:
            self.__save_current_chunk_if_valid()
            return True
        return False

    # TODO: here we should check for sentences (avoid missing punctuation before "Weiterlesen" etc.)
    def chunks_as_text(self):
        if self.chunks:
            return "\n".join([chunk.data for chunk in self.chunks])
        return ""


class Chunk:

    def __init__(self, data):
        self.data = data

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

