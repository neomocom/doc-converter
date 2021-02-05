import os
from html2text import HTMLParser, ChunkHTMLParser, Chunk, Html2TextChunksConverter


class TestHtml2TextConverter:

    def test_html_text_converter(self):
        with open(os.path.join(os.path.dirname(__file__), 'resources', 'energiesparen.html')) as f:
            content = f.read()
            text_chunks = Html2TextChunksConverter.to_text_chunks(content)
            assert len(text_chunks) == 223
            assert text_chunks[0].data == "Hausbau"


class TestChunkHTMLParser:

    parser = ChunkHTMLParser()

    def test_none_input(self):
        self.parser.parse(None)
        assert self.parser.chunks == []

    def test_blank_input(self):
        self.parser.parse(" ")
        assert self.parser.chunks == []

    def test_no_html_body(self):
        self.parser.parse("<html>foo</html>")
        assert self.parser.chunks == []

    def test_no_html_tag(self):
        self.parser.parse("<body>foo</body>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_multiple_parse_calls_work(self):
        self.parser.parse("<body>foo</body>")
        assert self.parser.chunks == [Chunk("foo")]
        self.parser.parse("<body>foo</body>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_ignore_head_content(self):
        self.parser.parse("<html><head><p>ignored</p></head><body><p>foo</p></body></html>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_ignore_blank_body_tag(self):
        self.parser.parse("<html><body> </body></html>")
        assert self.parser.chunks == []

    def test_body_without_child_tags(self):
        self.parser.parse("<html><body>foo</body></html>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_tag_content_is_trimmed(self):
        self.parser.parse("<html><body><p>\tfoo  \n</p></body></html>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_ignore_missing_end_tag(self):
        self.parser.parse("<html><body><p>foo</body>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_ignore_missing_end_tag_at_end(self):
        self.parser.parse("<body>foo")
        assert self.parser.chunks == [Chunk("foo")]

    def test_ignore_missing_start_tag(self):
        self.parser.parse("<html><body>foo</p></body>")
        assert self.parser.chunks == [Chunk("foo")]

    def test_nested_tags(self):
        self.parser.parse("<html><body>\r\n<div>  <div>\tfoo</div><div>bar<p>baz</p></div></div><p>baz</p></body></html>")
        assert self.parser.chunks == [Chunk("foo"), Chunk("bar"), Chunk("baz"), Chunk("baz")]

    def test_ignore_empty_nested_tag(self):
        self.parser.parse("<html><body><p> </p><span></span></body></html>")
        assert self.parser.chunks == []

    def test_data_without_opened_start_tag_is_parsed(self):
        self.parser.parse("<body>\t \r\n foo<p>bar</p></body>")
        assert self.parser.chunks == [Chunk("foo"), Chunk("bar")]

    def test_break_tags(self):
        self.parser.parse("<html><body><p>ideenplanet GmbH<br />Wesendonkstr. 63<br />81925 München, <u>Deutschland</u><br /> Telefonnummer: (0 89) 416 146 70<br />Telefax: (0 89) 416 146 710<br /></html></body>")
        assert self.parser.chunks == [Chunk(u"ideenplanet GmbH"), Chunk(u"Wesendonkstr. 63"),
                           Chunk(u"81925 München, Deutschland"), Chunk(u"Telefonnummer: (0 89) 416 146 70"),
                           Chunk(u"Telefax: (0 89) 416 146 710")]

    def test_single_flow_breaking_tag(self):
        self.parser.parse("<body><u>bu</u></body>")
        assert self.parser.chunks == [Chunk("bu")]

    def test_non_flow_breaking_tags(self):
        self.parser.parse("<body>ba<u>bu</u><p>foo<p><b><a>bar</a></b><span class=\"schnu\"><b><i>baz</i></b><font><em>wicked</em></font>faz<abbr>a<sup>b</sup></abbr></span></body>")
        assert self.parser.chunks == [Chunk("ba bu"), Chunk("foo"), Chunk("bar baz wicked faz a b")]

    def test_non_flow_breaking_tags_without_opening_start_tag(self):
        self.parser.parse("<body>foo<b>bar</b></br><b>baz</b></body>")
        assert self.parser.chunks == [Chunk("foo bar baz")]

    def test_convert_html_entities(self):
        self.parser.parse("<html><body><p class=foo>bar&nbsp;&shy; bla</p></body></html>")
        assert self.parser.chunks == [Chunk("bar\xa0\xad bla")]

    def test_style_and_script_tags_are_ignored(self):
        self.parser.parse("<html><body><style>{foo zeug: sliderkram} css</style><div>Divme</div><script type='text/javascript'>some script</body></html>")
        assert self.parser.chunks == [Chunk("Divme")]

    def test_ignore_xml_declarations_and_comments(self):
        self.parser.parse("<html><body><?xml version='1.0' encoding='character encoding' standalone='yes|no'?><?ignore>"
                          "<!DOCTYPE html PUBLIC \"-//W3C//DTD XHTML 1.0 Transitional//EN\""
                          " \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd\">"
                          "<p><!-- comment --></p>"
                          "<![CDATA[PFTEST0__COUNTER_6__:4:199:, PFTEST0__COUNTER_7__:4:199:]]></body></html>")
        assert self.parser.chunks == []

    def test_ignore_result_chunks_if_too_short(self):
        self.parser = ChunkHTMLParser(min_chunk_length=3)
        self.parser.parse("<html><body><a>.</a><div>ab</div>ba<tr>  ab </tr><div>abc<div><u>m- </u><p>  .\t\n\r</p><em>abc</em>d \t\r</body></html>")
        assert self.parser.chunks == [Chunk("abc"), Chunk("abc d")]
        self.parser.parse("<html><body><i>A</i>L<br/><u>L</u>E<em><b>S  </b></html>")
        assert self.parser.chunks == [Chunk("A L"), Chunk("L E S")]

    def test_parse_ideenplanet_impressum(self):
        with open(os.path.join(os.path.dirname(__file__), 'resources', 'ideenplanet_impressum.html')) as f:
            content = f.read()
            self.parser.parse(content)
            actualChunks = self.parser.chunks
            assert len(actualChunks) == 62
            assert Chunk("Wesendonkstr. 63") in actualChunks

    def test_parse_whole_energiesparen_page_as_string(self):
        with open(os.path.join(os.path.dirname(__file__), 'resources', 'energiesparen.html')) as f:
            content = f.read()
            self.parser.parse(content)
            chunks_as_text = self.parser.chunks_as_text()
            assert "Passivhausfenster sind Wohlfühlgaranten im Winter: Durch die Dreifachverglasung sinkt selbst bei" \
                   " Frost die innere Oberflächen­temperatur nicht unter 17 °C. Nur mit solchen Fenstern kann das" \
                   " Passivhaus genügend Wärme speichern und auf eine \"aktive\" Heizung verzichten."\
                   in chunks_as_text
            assert len(chunks_as_text.splitlines()) == 232

    def test_get_chunks_as_string(self):
        self.parser.parse("<html><body><p>foo<u>bla</u></p><br>bar</body></html>")
        assert self.parser.chunks_as_text() == "foo bla\nbar"

    def test_get_empty_chunks(self):
        assert ChunkHTMLParser().chunks_as_text() == ""

    class TestHTMLParser:
        html_parser = HTMLParser()

        def test_none_input(self):
            assert self.html_parser.to_text(None) is None

        def test_blank_input(self):
            assert self.html_parser.to_text("  ") is None

        def test_to_text_default(self):
            assert self.html_parser.to_text("<html><body><p>foo</p><div class=foo><span>Bär</span></div></body></html>") \
                   == "foo\nBär"

        def test_different_separator_text(self):
            assert (self.html_parser.to_text(
                "<html><body><p>foo</p><div class=foo><span>Bär</span></div></body></html>",
                text_separator=" ")) == "foo Bär"
