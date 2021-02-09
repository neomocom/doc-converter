from htmlchunks import Chunk, ArticleChunksExtractor


class TestArticleChunksExtractor:

    extractor = ArticleChunksExtractor(min_text_paragraph_length=10)

    def test_empty_chunks(self):
        assert self.extractor.extract([]) == []

    def test_no_longer_chunk(self):
        chunks = [Chunk("a", chunk_type=Chunk.headline_type), Chunk("b" * 5)]
        assert self.extractor.extract(chunks) == chunks

    def test_no_headline_before_longer_chunk(self):
        chunks = [Chunk("a" * 5), Chunk("a" * 5, chunk_type=Chunk.list_type), Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == [Chunk("b" * 11)]

    def test_longer_chunk_just_long_enough(self):
        chunks = [Chunk("a" * 5), Chunk("a" * 5), Chunk("b" * 10)]
        assert self.extractor.extract(chunks) == [Chunk("b" * 10)]

    def test_headline_too_far_away_from_longer_chunk(self):
        chunks = [Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a"),
                  Chunk("a"), Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == [Chunk("b" * 11)]

    def test_headline_searched_within_five_chunks_before_longer_chunk(self):
        chunks = [Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a"),
                  Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == chunks

    def test_all_chunks_before_headline_ignored(self):
        chunks = [Chunk("c"), Chunk("d", chunk_type=Chunk.list_type), Chunk("a", chunk_type=Chunk.headline_type),
                  Chunk("a"), Chunk("a"), Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == \
               [Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"), Chunk("b" * 11)]

    def test_first_headline_within_five_chunks_is_included(self):
        chunks = [Chunk("x", chunk_type=Chunk.headline_type), Chunk("c", chunk_type=Chunk.headline_type),
                  Chunk("a"), Chunk("a"), Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == [Chunk("c", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"),
                                                  Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"),
                                                  Chunk("b" * 11)]

    def test_only_chunk_is_longer(self):
        chunks = [Chunk("b" * 11)]
        assert self.extractor.extract(chunks) == [Chunk("b" * 11)]

    def test_first_chunk_is_longer_followed_by_many_chunks(self):
        chunks = [Chunk("b" * 11), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a"), Chunk("a")]
        assert self.extractor.extract(chunks) == chunks

    def test_longer_chunk_is_followed_by_headline_chunks(self):
        chunks = [Chunk("a"), Chunk("b" * 11), Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"),
                  Chunk("a", chunk_type=Chunk.headline_type), Chunk("a"), Chunk("a"), Chunk("a")]
        assert self.extractor.extract(chunks) == [Chunk("b" * 11), Chunk("a", chunk_type=Chunk.headline_type),
                                                  Chunk("a"), Chunk("a"),Chunk("a", chunk_type=Chunk.headline_type),
                                                  Chunk("a"), Chunk("a"), Chunk("a")]

    def test_default_for_min_paragraph_length(self):
        chunks = [Chunk("b" * 199), Chunk("a"), Chunk("b" * 200)]
        assert ArticleChunksExtractor().extract(chunks) == [Chunk("b" * 200)]
