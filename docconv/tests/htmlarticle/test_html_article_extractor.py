import os
import datetime

import pytest
from dateutil.tz import tzutc, tzoffset
from lxml import etree
from htmlarticle import HtmlArticleExtractor

SOURCE_URL = 'http://foo.de'


class TestHtmlArticleExtractor:

    extractor = HtmlArticleExtractor()

    def test_no_html_leads_to_empty_article_text(self):
        article = self.extractor.extract(None, SOURCE_URL)
        assert article.text == ""

    def test_emtpy_html_leads_to_empty_article_text(self):
        article = self.extractor.extract("", SOURCE_URL)
        assert article.text == ""

    def test_blank_html_leads_to_empty_article_text(self):
        article = self.extractor.extract(" \t ", SOURCE_URL)
        assert article.text == ""

    def test_no_html_leads_to_empty_article_attributes(self):
        article = self.extractor.extract(None, SOURCE_URL)
        assert article.title == ''
        assert article.authors == []
        assert article.publication_date is None
        assert article.image_urls == []

    def test_minimalistic_html_leads_to_empty_article_text(self):
        article = self.extractor.extract("<html><body><p></p></body></html>", SOURCE_URL)
        assert article.text == ''

    def test_minimalistic_html_leads_to_empty_article_attributes(self):
        article = self.extractor.extract("<html><body><p></p></body></html>", SOURCE_URL)
        assert article.title == ''
        assert article.authors == []
        assert article.publication_date is None
        assert article.image_urls == []

    def test_html_article_text_is_extracted_and_stripped(self):
        with open(get_test_resource('valid_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert html.startswith('<!DOCTYPE html>')
            assert article.text.startswith('As the population of')
            assert article.text.endswith('Research and Quality.')

    def test_html_shortened_article_title_is_extracted(self):
        with open(get_test_resource('valid_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.title == 'ECHO-CT: An Interdisciplinary Videoconference Model for Identifying Potential' \
                                    ' Postdischarge Transition-of-Care Events'

    def test_html_article_text_is_extracted_from_image_article(self):
        with open(get_test_resource('image_in_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.text.startswith('In a time of tremendous uncertainty,')
            assert article.text.endswith('She is a member of SHM’s Practice Analysis Committee.')

    def test_authors_extracted_after_keyword_above_top_node_and_on_different_level(self):
        with open(get_test_resource('valid_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Mariana R Gonzalez', 'Lauren Junge-Maughan', 'Lewis A Lipsitz', 'Amber Moore']

    def test_extract_authors_keyword_in_same_tag_before_top_node(self):
        with open(get_test_resource('authors_and_keyword_in_same_tag_no_class_before_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ["Max Power"]

    def test_extract_authors_keyword_in_same_tag_after_top_node_over_before_top_node(self):
        with open(get_test_resource('authors_and_keyword_in_same_tag_before_and_after_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ["Heather Nye"]

    def test_authors_found_in_span_with_keyword_before_top_node(self):
        with open(get_test_resource('authors_and_keyword_in_span_before_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ["Sarah Warren"]

    def test_authors_before_top_node_are_only_a_fallback(self):
        with open(get_test_resource('authors_and_keyword_before_and_after_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Mariana R Gonzalez', 'Lauren Junge-Maughan', 'Lewis A Lipsitz', 'Amber Moore',
                                       'ASHA working in SNFs face a more prolonged recovery.'] #FIXME!!

    def test_authors_in_li_plus_a_with_authors_class_before_top_node(self):
        with open(get_test_resource('authors_li_a_with_authors_tag_before_top_node_different_level.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Saori Kijima', 'Kazuya Tomihara', 'Masami Tagawa']

    def test_authors_in_div_with_authors_class_before_top_node(self):
        with open(get_test_resource('authors_in_div_with_authors_class_before_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Max Early Power']

    def test_authors_in_div_with_authors_class_extracted_after_top_wins(self):
        with open(get_test_resource('authors_in_div_with_authors_class_after_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Max Power', 'Mary Power']

    def test_authors_in_a_tag_with_authors_class_before_top_node(self):
        with open(get_test_resource('authors_in_a_with_authors_class_before_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Marion C. Leaman', 'Lisa A. Edmonds']

    def test_authors_in_a_tag_with_authors_class_after_top_node_beats_before_node(self):
        with open(get_test_resource('authors_in_a_tag_with_authors_class_before_and_after_top_node.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Anli Yue Zhou', 'Maria Panagioti', 'Aneez Esmail', 'Raymond Agius',
                                       'Martie Van Tongeren', 'Peter Bower']

    def test_authors_under_multiple_tags_with_author_class_are_deduplicated(self):
        with open(get_test_resource('authors_in_multiple_tags_with_author_class.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Elizabeth A Ungerman', 'Keith M Vogt', 'Tetsuro Sakai', 'David G Metro',
                                       'Phillip S Adams']

    def test_authors_with_author_class_in_a_takes_precedence_over_spans_that_are_joined(self):
        with open(get_test_resource('authors_in_a_with_first_and_last_name_span_child_with_author_class.html'), 'r')\
                as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Cristina Nituica', 'Oana Alina Bota', 'John Blebea']

    def test_div_tag_with_authors_class_not_inspected_if_authors_found_in_other_tags(self):
        with open(get_test_resource('authors_in_a_but_author_info_in_div.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Lawrence M. Lewis', 'Evan Schwarz', 'Randall Jotte', 'Colin P. West']

    def test_li_tag_with_authors_affiliation_class_ignored(self):
        with open(get_test_resource('author_affiliation_li_ignored.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == ['Elizabeth A. Samuels', 'Dowin H. Boatright', 'Ambrose H. Wong',
                                       'Laura D. Cramer', 'Mayur M. Desai', 'Michael T. Solotke',
                                       'Darin Latimore', 'Cary P. Gross']

    def test_div_tag_with_related_authors_class_ignored(self):
        with open(get_test_resource('ignore_related_authors_divs.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.authors == []

    def test_no_author_keyword_found_in_top_node(self):
        top_node = etree.XML('<div><p>schnitzel</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_author_after_keyword_without_semicolon_is_not_enough(self):
        top_node = etree.XML('<div><p>By Max Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    @pytest.mark.parametrize("keyword", ["By", "Author", "Authors", "Author(s)"])
    def test_author_after_keywords_and_semicolon_extracted(self, keyword):
        top_node = etree.XML(f'<div><p>{keyword}: Max Power, Maya Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power', 'Maya Power']

    def test_inspect_only_first_tag_with_keyword_followed_by_author(self):
        top_node = etree.XML(f'<div><p>Authors: Max Power</p><p>Authors: Igore Ignore</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_author_after_keyword_is_stripped(self):
        top_node = etree.XML('<div><p>By:  Max Power \t  </p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_author_after_keyword_does_not_need_leading_space(self):
        top_node = etree.XML('<div><p>Author:Max Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_author_after_keyword_found_if_only_newline_in_between(self):
        top_node = etree.XML('<div><p>Author(s): Max\nPower</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_author_after_keyword_not_found_tag_in_author_name(self):
        top_node = etree.XML('<div><p>Author: <em>Max</em> Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_no_authors_extracted_if_keyword_only_followed_by_blanks(self):
        top_node = etree.XML('<div><p>By:  \t  </p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_no_authors_extracted_if_keyword_before_author_not_at_start(self):
        top_node = etree.XML('<div><p>there is a By: Max Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_no_authors_extracted_if_keyword_before_author_not_upper_case(self):
        top_node = etree.XML('<div><p>by: Max Power</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_author_after_keyword_found_if_newline_in_between(self):
        top_node = etree.XML('<div><p>By: Max \n\r \r \n Power \n </p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_author_after_keyword_is_validated(self):
        top_node = etree.XML('<div><p>By: Max \t Power, \n Mr. Thompson , MD, some stuff, M. D </p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power', 'Mr. Thompson']

    def test_author_last_name_comma_first_name_is_not_extracted_correctly(self):
        top_node = etree.XML('<div><p>By: Power, Max, Power, Max Peter</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Peter']

    def test_tag_contains_only_author_keyword_present(self):
        top_node = etree.XML('<div><p>By:</p></div>')
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    @pytest.mark.parametrize("keyword", ["By", "By:", "Author", "Author:", "Authors", "Authors:",
                                         "Author(s)", "Author(s):"])
    def test_span_only_containing_keyword_followed_by_dd_with_author(self, keyword):
        top_node = etree.XML(f"""<div class="pane-content">
          <span class="field-label">{keyword}</span>
      
      <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">Kelly April Tyrrell, MD</a></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Kelly April Tyrrell']

    def test_span_only_containing_keyword_takes_precedence_over_keyword_and_author_in_same_tag(self):
        top_node = etree.XML(f"""<div class="pane-content">
             <span class="field-label">By: Igor Ignore</span>
             <span class="field-label">By:</span>
         <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">Max Power</a></dd>
         </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_span_only_containing_keyword_followed_by_dd_with_multiple_authors(self):
        top_node = etree.XML("""<div class="pane-content">
          <span class="field-label">By</span>
      <dd class="field field-name-field-article-authors "><strong>Kelly April Tyrrell</strong>
        <strong>Max Power</strong>
        <i class="envelope">::before</i>
        <strong>M TooShort</strong></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Kelly April Tyrrell', 'Max Power']

    def test_span_only_containing_keyword_followed_by_none(self):
        top_node = etree.XML("""<div class="pane-content">
          <div>
          <span class="field-label">By:</span>
          </div>
          <span>Too far Away</span>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_span_only_containing_keyword_followed_by_empty_dd(self):
        top_node = etree.XML("""<div class="pane-content">
          <span class="field-label">By</span>
      <dd class="field field-name-field-article-authors "></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    @pytest.mark.parametrize("keyword", ["By", "By:", "Author", "Author:", "Authors", "Authors:",
                                         "Author(s)", "Author(s):"])
    def test_span_containing_spaces_plus_keyword_followed_by_dd_with_author(self, keyword):
        top_node = etree.XML(f"""<div class="pane-content">
          <span class="field-label">
        {keyword}  
      </span>
      <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">K. \r\n Tyrrell, Max Power</a></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['K. Tyrrell', 'Max Power']

    def test_inspect_only_first_keyword_span_followed_by_dd_with_author(self):
        top_node = etree.XML(f"""<div class="pane-content">
          <span class="field-label"> Authors </span>
      <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">Max Power</a></dd>
        <span class="field-label"> Authors </span>
      <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">Igor Ignore</a></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power']

    def test_ignore_other_tag_than_span_that_contains_keyword_only(self):
        top_node = etree.XML("""<div class="pane-content">
          <strong>By:</strong>
      <dd class="field field-name-field-article-authors "><a href="/authors/tyrrell">Kelly April Tyrrell</a></dd>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_span_that_contains_keyword_only_followed_by_other_than_dd(self):
        top_node = etree.XML("""<div class="pane-content">
          <span>Authors:</span>
      <div class="field field-name-field-article-authors "><a href="/authors/tyrrell">Kelly April Tyrrell</a></div>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == []

    def test_span_containing_keyword_followed_by_dd_with_nested_author(self):
        top_node = etree.XML("""<div class="pane-content">
          <span class="field-label">By  </span>
      <dd class="field field-name-field-article-authors "><span>
       <a href="/authors/tyrrell"><strong>K. \r\n Tyrrell, Max Power</strong></a></span></dd></div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['K. Tyrrell', 'Max Power']

    def test_span_containing_keyword_followed_by_dd_with_multiple_authors_under_one_nested_tag(self):
        top_node = etree.XML("""<div class="pane-content">
          <span class="field-label">By  </span>
      <dd class="field field-name-field-article-authors "><span>
       <a href="/authors/tyrrell">K. Tyrrell<strong>,</strong>Max Power</a></span></dd></div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['K. Tyrrell', 'Max Power']

    def test_span_containing_keyword_followed_by_dd_with_author_partially_nested_deeper(self):
        top_node = etree.XML("""<div class="pane-content">
             <span class="field-label">By  </span>
         <dd class="field field-name-field-article-authors "><span>
          <a href="/authors/tyrrell"><strong><i>\n   </i><em>K.</em>Tyrrell, Max Power</strong></a></span></dd></div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['K. Tyrrell', 'Max Power']

    def test_if_first_element_after_keyword_span_is_not_dd_following_siblings_text_extracted(self):
        top_node = etree.XML("""<div class="pane-content">
        <div>
          <span>Author(s):</span>
          <em>Max \n \r  Power, MD</em>
          <span><em>Mary Power </em></span>
          <em>M Tooshort</em>
      <dd class="field field-name-field-article-authors "><a href="/authors/igor">Ignore Igor</a></dd>
      <p>Marty McFly</p>
      </div>
      </div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Max Power', 'Marty McFly']

    def test_element_after_keyword_span_ul_li_is_searched_for_authors(self):
        top_node = etree.XML("""<div><span>By</span>
        <ul aria-label="authors" class="rlist--inline loa comma">
        <li><span>Sarah Warren, Max \n Power, MD</span></li></ul></div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Sarah Warren', 'Max Power']

    def test_element_after_keyword_span_ul_li_is_searched_for_nested_authors(self):
        top_node = etree.XML("""<div><span>By</span>
        <ul aria-label="authors" class="rlist--inline loa comma">
        <li><span><a href="/action/doSearch?field=SarahWarren"><span>Sarah Warren</span></a>
        <sup></sup></span></li>
        <li><span>Max <em>Power</em></span></li></ul></div>""")
        assert self.extractor.extract_author_by_keyword_from_article(top_node) == ['Sarah Warren', 'Max Power']

    def test_a_with_authors_class_but_no_text(self):
        top_node = etree.XML("<div><a class='authorsome'></a></div>")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == []

    def test_a_with_authors_class_but_no_text_nested(self):
        top_node = etree.XML("<div><a class='authorsome'><span></span><div> <b></b></div></a></div>")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == []

    def test_a_with_authors_class_flat_text_no_author(self):
        top_node = etree.XML("<div class='authorsome'><a class='authorsome'>foo</a></div>")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == []

    def test_a_with_authors_class_flat_text_author(self):
        top_node = etree.XML("<div><a class='authorsome'>Max Power</a></div>")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power']

    def test_a_with_authors_class_nested_text_author(self):
        top_node = etree.XML("<div><a class='authorsome'><span> Max Power </span></a></div>")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power']

    def test_a_with_authors_class_multiple_authors_not_separated(self):
        top_node = etree.XML("""<div><a class='authorsome'><span> Max Power</span>
        <span>Mary Power </span></a></div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power Mary Power']

    def test_a_with_authors_class_multiple_authors_separated(self):
        top_node = etree.XML("""<div><a class='authorsome'>
        <span> Max Power</span>and<span>Mary Power </span></a></div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power', 'Mary Power']

    def test_multiple_a_tags_with_authors_class(self):
        top_node = etree.XML("""<div><a class='authorsome'>
        Max <span>Power</span></a> and then <a class='author'><span>Mary</span><span><h1>Power</h1></span></a></div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power', 'Mary Power']

    def test_multiple_nested_a_tags_with_authors_class(self):
        top_node = etree.XML("""<div><a class='authorsome'>
           Max <span>Power</span>and <a class='author'><span>Mary</span><span><h1>Power</h1></span></a></a> </div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node)\
               == ['Max Power', 'Mary Power', 'Mary Power']

    def test_a_with_authors_class_ignores_stripped_one_char_texts(self):
        top_node = etree.XML("""<div><a class='shmauthor'>
        Max <span> a </span><b>1</b> <div>#</div> <span>Power</span><b>MD</b></a> </div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Max Power MD']

    def test_a_with_authors_class_does_not_ignore_tag_with_single_separator(self):
        top_node = etree.XML("""<div><a class='shmauthor'>
        Max <span> , </span> <span>Power</span><b>MD</b></a> </div>""")
        assert self.extractor.extract_authors_from_a_with_author_class(top_node) == ['Power MD']

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_author_class_but_no_text(self, tag):
        top_node = etree.XML(f"<div><{tag} class='authorsome'></{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == []

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_but_no_text_nested(self, tag):
        top_node = etree.XML(f"<div><{tag} class='authorsome'><span></span><div> <b> </b></div></{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == []

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_with_flat_text_but_no_author(self, tag):
        top_node = etree.XML(f"<div><{tag} class='authorsome'>foo bar</{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == []

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_with_nested_text_but_no_author_in_same_tag(self, tag):
        top_node = etree.XML(f"<div><{tag} class='authorsome'><span>Max</span><div>Power</div> </{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == []

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_with_deeply_nested_text_but_no_author_in_same_tag(self, tag):
        top_node = etree.XML(f"<div><{tag} class='authorsome'><span>Max <div>Power</div></span> </{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == []

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_with_flat_text_and_author(self, tag):
        top_node = etree.XML(f"<div><{tag} class='author'>Max Power</{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == ['Max Power']

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_li_or_span_with_authors_class_with_nested_text_and_author(self, tag):
        top_node = etree.XML(f"<div><{tag} class='author'><span><div>Max Power</div></span></{tag}></div>")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node) == ['Max Power']

    @pytest.mark.parametrize("tag", ["li", "span"])
    def test_multiple_li_or_span_with_authors_class_and_multiple_authors(self, tag):
        top_node = etree.XML(f"""<div><{tag} class='author'>Mary Power<span><div>Max Power</div></span></{tag}>
        <div><{tag} class='shmauthor'> Macy Power and Master   Power </{tag}></div> </div>""")
        assert self.extractor.extract_authors_from_li_or_span_with_author_class(top_node)\
               == ['Mary Power', 'Max Power', 'Macy Power', 'Master Power']

    def test_any_spaces_within_author_are_normalized(self):
        assert self.extractor.get_author_names('Max \t   Power') == ['Max Power']

    def test_single_author_extracted(self):
        assert self.extractor.get_author_names('Max Power') == ['Max Power']

    def test_one_word_authors_are_not_valid(self):
        assert self.extractor.get_author_names('Power') == []

    @pytest.mark.parametrize("no_author", ['Max P', 'M. P -', 'Li X', 'Kim S H', 'M Power', 'Et al.'])
    def test_authors2words_with_less_than2valid_chars_disallowed(self, no_author):
        assert self.extractor.get_author_names(no_author) == []

    @pytest.mark.parametrize("no_author", ['M1x Power', 'Max P0wer'])
    def test_authors_digits_not_allowed(self, no_author):
        assert self.extractor.get_author_names(no_author) == []

    def test_author_first_word_needs_to_start_with_uppercase(self):
        assert self.extractor.get_author_names('max Power, "Max Power", (Max Power)') == []

    def test_author_after_first_word_with_dot_space_is_needed(self):
        assert self.extractor.get_author_names('M.Power') == []

    def test_second_author_word_can_start_with_dot_and_come_late_to_the_party(self):
        assert self.extractor.get_author_names('Max power plus then some .More') == ['Max power plus then some .More']

    @pytest.mark.parametrize("author", ['M. Power', 'M. P.', 'M- P-', 'Li Xu', 'Laura C- et al.', 'Alpesh N.Amin'])
    def test_author_with_2valid_words(self, author):
        assert self.extractor.get_author_names(author) == [author]

    def test_author_with_2valid_words_with_special_letters(self):
        assert self.extractor.get_author_names('Alán Briöñeß') == ['Alán Briöñeß']

    def test_author_with_double_names(self):
        assert self.extractor.get_author_names('Lauren Junge-Maughan') == ['Lauren Junge-Maughan']
        assert self.extractor.get_author_names('De La Hoya') == ['De La Hoya']

    def test_author_with_hyphen_names(self):
        assert self.extractor.get_author_names('M. O’Donnell') == ['M. O’Donnell']

    @pytest.mark.parametrize("author", ['Mariana Anna R Gonzalez - Caballero MD', 'Lewis A Lipsitz', 'Burroughs - Ray'])
    def test_author_with_names_having_single_char_in_between(self, author):
        assert self.extractor.get_author_names(author) == [author]

    def test_multiple_authors_separated_by_comma_extracted(self):
        assert self.extractor.get_author_names('Max Power, Mr. Thompson') == ['Max Power', 'Mr. Thompson']

    def test_multiple_authors_separated_by_and_extracted(self):
        assert self.extractor.get_author_names('Max Power and Mr. Thompson') == ['Max Power', 'Mr. Thompson']

    def test_multiple_authors_separated_by_and_with_word_boundary_not_extracted(self):
        assert self.extractor.get_author_names('Rhode Island') == ['Rhode Island']
        assert self.extractor.get_author_names('Randall Jotte') == ['Randall Jotte']
        assert self.extractor.get_author_names('Max andy Power') == ['Max andy Power']

    def test_authors_are_stripped(self):
        assert self.extractor.get_author_names(' Max Power ,   Mr. Thompson  ') == ['Max Power', 'Mr. Thompson']

    def test_by_word_is_stripped_from_author(self):
        assert self.extractor.get_author_names('By Max By Power') == ['Max By Power']
        assert self.extractor.get_author_names('by Max By Power') == ['Max By Power']
        assert self.extractor.get_author_names('Bymax Power') == ['Bymax Power']

    def test_by_word_is_stripped_before_validating_author(self):
        assert self.extractor.get_author_names('By Max') == []

    def test_authors_can_be_extracted_over_multiple_lines(self):
        assert self.extractor.get_author_names('Max  \n Power, \n  Mr. \r Thompson  ') == ['Max Power', 'Mr. Thompson']

    @pytest.mark.parametrize("no_author", ['M. Power Center', 'Max City Power', 'Corresponding Author',
                                           'For authors and So', 'Marty McFly from Mdedge News',
                                           'Max Power (society Of some Some)', 'The community and Some',
                                           'ABC-GmbH and Some', 'ABC/Inc.', 'ABC Ltd - AG', 'ABC Corp. ',
                                           'D. S, MD, Executive Director,'
                                           ' Executive Leadership in Academic Medicine,'
                                           ' Associate Dean of Faculty Development,'
                                           ' Drexel University College of Medicine', 'Service Mary'])
    def test_author_containing_special_words_are_discarded(self, no_author):
        assert self.extractor.get_author_names(no_author) == []

    def test_author_cannot_have_more_than_10_words(self):
        assert self.extractor.get_author_names('Max Power, Typically Stuff like this is not An Shmauthor name any mo.')\
               == ['Max Power']

    def test_author_containing_special_words_as_infix_are_ok(self):
        assert self.extractor.get_author_names('Max Shmnews,Maya Inca,  Mr.  Corpski') \
               == ['Max Shmnews', 'Maya Inca', 'Mr. Corpski']

    def test_valid_images_are_extracted_within_article(self):
        with open(get_test_resource('image_in_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.image_urls == \
                ['https://cdn.mdedge.com/files/s3fs-public/styles/medium/public/Kurian_Linda_NY_web.jpg',
                 'https://cdn.mdedge.com/files/s3fs-public/149981_Fig1_Trends_web.jpg',
                 'https://cdn.mdedge.com/files/s3fs-public/149981_Fig2_Avg compensation_web.jpg',
                 'https://cdn.mdedge.com/files/s3fs-public/149981_Fig3_Amt financ supp_web.jpg']

    def test_images_are_extracted_only_once_keeping_the_order(self):
        with open(get_test_resource('image_duplicates_in_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.image_urls == \
            ['https://cdn.mdedge.com/files/s3fs-public/styles/medium/public/Zia_Sareer_web.jpg',
             'https://cdn.mdedge.com/files/s3fs-public/149518_fig1.jpg',
             'https://cdn.mdedge.com/files/s3fs-public/149518_fig2.jpg']

    def test_no_image_could_be_extracted_from_article(self):
        with open(get_test_resource('no_image_in_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.image_urls == []

    def test_svgs_and_images_with_no_source_are_ignored(self):
        with open(get_test_resource('invalid_images_in_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.image_urls == \
                   ['http://foo.de/sites/all/themes/custom/medstat_jhm/img/shm_logo_micro.png',
                    'https://cdn.mdedge.com/files/s3fs-public/149981_Fig1_Trends_web.jpg',
                    'https://cdn.mdedge.com/files/s3fs-public/149981_Fig2_Avg '
                    'compensation_web.jpg']

    def test_images_below_article_are_ignored(self):
        with open(get_test_resource('images_below_article.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.image_urls == []

    def test_no_valid_publish_date_found(self):
        html = '''<html><head><meta id="meta-publication_date" name="fo_publication_date" content="foo"/>
                <meta property="article:published_time" content="2019-28-15 12:28:30"/></head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date is None
        assert article.publication_date_display is None

    def test_no_publish_date_found(self):
        html = "<html></html"
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date is None
        assert article.publication_date_display is None

    def test_publish_date_found_by_property_in_meta(self):
        with open(get_test_resource('publish_date_in_meta_tags.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.publication_date == datetime.datetime(2020, 1, 14, 11, 52, 37, tzinfo=tzutc())
            assert article.publication_date_display == 'January 14, 2020'

    def test_publish_date_found_by_first_meta_tag_name_in_order(self):
        with open(get_test_resource('publish_date_in_2_meta_tags.html'), 'r') as file:
            html = file.read()
            article = self.extractor.extract(html, SOURCE_URL)
            assert article.publication_date == datetime.datetime(2018, 2, 1, 0, 0)
            assert article.publication_date_display == 'February 01, 2018'

    def test_year_only_publish_date(self):
        html = '<html><head><meta id="meta-publication_date" name="fo_publication_date" content="2020"/> </head></html>'
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2020, 1, 1, 0, 0)
        assert article.publication_date_display == '2020'

    def test_year_and_month_only_publish_date(self):
        html = '''<html><head><meta id="meta-publication_date" name="citation_publication_date" content="2020/11"/> 
                       </head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2020, 11, 1, 0, 0)
        assert article.publication_date_display == 'November, 2020'

    def test_publish_date_without_year(self):
        html = '''<html><head><meta id="meta-publication_date" name="publication_date" content="01-3T17:27:37-01:00"/> 
               </head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(1970, 1, 3, 17, 27, 37, tzinfo=tzoffset(None, -3600))
        assert article.publication_date_display == 'January 03'

    def test_publish_date_with_shortened_year(self):
        html = '''<html><head><meta id="meta-publication_date" itemprop="datePublished" content="12/12/13"/> 
               </head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2013, 12, 12, 0, 0)
        assert article.publication_date_display == 'December 12, 2013'

    def test_publish_date_found_in_ld_json_script(self):
        html = '''<html><head>
                        <script type="application/ld+json"> {"@context": "http:\/\/schema.org", "@type": "NewsArticle",
                                    "datePublished": "2021-07-12T12:31:00Z",
                                    "articleSection": "Risikolebensversicherung"
                                    } 
                        </script></head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2021, 7, 12, 12, 31, tzinfo=tzutc())
        assert article.publication_date_display == 'July 12, 2021'

    def test_publish_date_searched_in_all_ld_json_script_in_body(self):
        html = '''<html><head><script type="application/ld+json"> {"@context": "http:\/\/schema.org", "@type": "NewsArticle",
                                    "articleSection": "Risikolebensversicherung"
                                    } 
                        </script>
                        <script type="application/ld+json"> {BROKEN "http:\/\/schema.org", "@type": "NewsArticle",
                                    "datePublished": "2000-07-12T12:31:00Z"
                                    } 
                        </script></head><body>
                        <script type="application/ld+json"> {"@context": "http:\/\/schema.org", "@type": "NewsArticle",
                                    "datePublished": "2021-07-12T12:31:00Z"
                                    } 
                        </script></body></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2021, 7, 12, 12, 31, tzinfo=tzutc())
        assert article.publication_date_display == 'July 12, 2021'

    def test_publish_date_not_found_in_ld_json_script(self):
        html = '''<html><head>
                        <script type="application/ld+json"> {"@context": "http:\/\/schema.org", "@type": "NewsArticle",
                                    "dateModified": "2021-07-12T12:31:00Z",
                                    "articleSection": "Risikolebensversicherung"
                                    } 
                        </script></head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date is None
        assert article.publication_date_display is None

    def test_publish_date_not_parsed_from_invalid_ld_json_script(self):
        html = '''<html><head>
                        <script type="application/ld+json"> NO JSON:  "datePublished": "2021-07-12T12:31:00Z" 
                        </script></head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date is None
        assert article.publication_date_display is None

    def test_publish_date_meta_tags_wins_over_ld_json_script(self):
        html = '''<html><head>
                    <meta id="meta-publication_date" itemprop="datePublished" dateTime="12/12/13"/>
                       <script type="application/ld+json"> {"@context": "http:\/\/schema.org", "@type": "NewsArticle",
                                    "datePublished": "2021-07-12T12:31:00Z",
                                    "articleSection": "Risikolebensversicherung"
                                    } 
                        </script></head></html>'''
        article = self.extractor.extract(html, SOURCE_URL)
        assert article.publication_date == datetime.datetime(2013, 12, 12, 0, 0)
        assert article.publication_date_display == 'December 12, 2013'


def get_test_resource(file_name):
    return os.path.join(os.path.dirname(__file__), 'resources', file_name)

