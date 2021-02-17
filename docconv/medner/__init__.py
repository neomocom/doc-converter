import spacy

MINIMAL_CONCEPT_LENGTH = 3


class MedicalConceptsExtractor:

    def __init__(self):
        self.nlp = spacy.load("en_ner_bc5cdr_md")

    def extract(self, text):
        if not text:
            return []
        document = self.nlp(text)
        seen_concepts = set()
        concepts = []
        for entity in document.ents:
            if entity.label_ != 'DISEASE' or len(entity.text) < MINIMAL_CONCEPT_LENGTH:
                continue
            concept = self.normalize_spaces(entity.text.lower())
            if concept not in seen_concepts:
                concepts.append(Concept(concept, entity.label_))
                seen_concepts.add(concept)
        return concepts

    @staticmethod
    def normalize_spaces(text):
        return " ".join(text.split())


class Concept:

    def __init__(self, text, entity_type):
        self.text = text
        self.entity_type = entity_type

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        return type(other) is type(self) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)
