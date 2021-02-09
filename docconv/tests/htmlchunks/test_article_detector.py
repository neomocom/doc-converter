from htmlchunks import Chunk, ArticleDetector


class TestArticleDetector:

    def test_empty_chunks(self):
        assert not ArticleDetector().is_article([])

    def test_that_min_chunk_length_is_respected(self):
        assert not ArticleDetector(min_article_length=5, min_chunk_length=1).is_article([Chunk("bu"), Chunk("ba")])

    def test_that_min_article_length_is_respected(self):
        assert not ArticleDetector(min_article_length=3, min_chunk_length=3).is_article([Chunk("bu"), Chunk("ba")])

    def test_min_article_length_and_min_chunk_length_is_exceeded(self):
        assert ArticleDetector(min_article_length=5, min_chunk_length=2).is_article([Chunk("buz"), Chunk("baz")])

    def test_min_article_length_and_partially_min_chunk_length_is_exceeded(self):
        assert ArticleDetector(min_article_length=5, min_chunk_length=3).is_article([Chunk("batzen"), Chunk("ba")])

    def test_exact_chunk_length(self):
        assert ArticleDetector(min_article_length=1, min_chunk_length=2).is_article([Chunk("bu"), Chunk("ba")])

    def test_exact_article_length(self):
        assert ArticleDetector(min_article_length=4, min_chunk_length=0).is_article([Chunk("bu"), Chunk("ba")])

    def test_min_article_length_default(self):
        assert ArticleDetector(min_chunk_length=0).is_article([Chunk("b" * 1000)])
        assert not ArticleDetector(min_chunk_length=0).is_article([Chunk("b" * 999)])

    def test_min_chunk_length_default(self):
        assert ArticleDetector(min_article_length=1).is_article([Chunk("b" * 50)])
        assert not ArticleDetector(min_article_length=1).is_article([Chunk("b" * 49)])
