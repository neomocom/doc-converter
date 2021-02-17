from medner import MedicalConceptsExtractor, Concept


class TestMedicalConceptExtractor:

    extractor = MedicalConceptsExtractor()

    def test_none_text_emtpy_concepts(self):
        assert self.extractor.extract(None) == []

    def test_empty_text_emtpy_concepts(self):
        assert self.extractor.extract("") == []

    def test_text_with_no_concepts(self):
        assert self.extractor.extract("foo bar") == []

    def test_only_diseases_are_included(self):
        text = "•Pathophysiology and tobacco smoke and aspirin and pulmonary hypertension"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_are_deduplicated(self):
        text = "pulmonary hypertension and more pulmonary hypertension"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_are_lower_cased_for_deduplication(self):
        text = "pulmonary hypertension and more Pulmonary Hypertension"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_in_between_whitespaces_are_normalized_for_deduplication(self):
        text = " pulmonary  hypertension   and more pulmonary\thypertension  \n"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_are_lower_cased(self):
        text = "Pulmonary Hypertension"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_at_beginning_include_prior_short_word_starting_with_b(self):
        text = "b pulmonary hypertension foo"
        entities = self.extractor.extract(text)
        assert entities == [Concept("b pulmonary hypertension", "DISEASE")]

    def test_concepts_in_between_spaces_are_normalized(self):
        text = "a pulmonary \t\n       hypertension foo"
        entities = self.extractor.extract(text)
        assert entities == [Concept("pulmonary hypertension", "DISEASE")]

    def test_concepts_are_split_for_multi_spaces_in_between_and_extra_spaces_around(self):
        text = "a  pulmonary    hypertension "
        entities = self.extractor.extract(text)
        assert entities == [Concept("hypertension", "DISEASE")]

    def test_concepts_order_from_text_is_kept(self):
        text = "myocardial infarction and pulmonary hypertension and chest pain"
        entities = self.extractor.extract(text)
        assert entities == [Concept("myocardial infarction", "DISEASE"), Concept("pulmonary hypertension", "DISEASE"),
                            Concept("chest pain", "DISEASE")]

    def test_extraction_many_diseases(self):
        text = """Pulmonary Hypertension Parth Shah, DO\nDefinition: Resting mean pulmonary artery pressure (mPAP)
         >20 mmHg (normal is 8-20 mmHg) and an\nelevated pulmonary vascular resistance (PVR) 3 Woods units measured
          on right heart catheterization.\nThe World Health Organization breaks down pulmonary hypertension into
           5 classes.\nGroup 1: Pulmonary Arterial Hypertension\n• Etiology: Idiopathic,
           heritable (BMPR2 gene mutation), connective tissue disease, HIV infection,
                schistosomiasis (common worldwide), drugs/toxins
                \n•Pathophysiology: hyperplasia and hypertrophy of all 3 walls of small pulmonary arterioles\n
                • Imaging: Chest x-ray can show enlargement of central pulmonary arteries and right heart border
                \n    prominence.
                Chronic obstructive pulmonary\n disease (COPD) is a heterogeneous group of respiratory conditions,
         predominantly composed of chronic bronchitis and emphysema. Exposure to tobacco smoke is the main risk factor"""
        entities = self.extractor.extract(text)
        assert entities == [Concept('pulmonary hypertension', 'DISEASE'), Concept('idiopathic, heritable', 'DISEASE'),
                            Concept('connective tissue disease', 'DISEASE'), Concept('hiv infection', 'DISEASE'),
                            Concept('hyperplasia and hypertrophy', 'DISEASE'),
                            Concept('enlargement of central pulmonary arteries and right heart', 'DISEASE'),
                            Concept('chronic obstructive pulmonary disease', 'DISEASE'), Concept('copd', 'DISEASE'),
                            Concept('bronchitis', 'DISEASE'), Concept('emphysema', 'DISEASE')]

    def test_extraction_on_text_with_fluff(self):
        text = '''SAN DIEGO — As a hospitalist, the best approach to the comanagement of patients is to define your
         boundaries from the start and revisit those boundaries frequently.
         Ask other members of the care team specific questions, such as: What parts of this patient's care are your
         responsibility? What parts of the care are mine? How are we going to decide who does what?\n
         “If you don't know what you're doing when you're seeing the patients, if you don't have a coherent and mutually
         agreed upon vision for how you're going to make the care better, I'm not sure that you're actually doing
         anything other than showing up,” Dr. Eric M. Siegal said at the annual meeting of the Society of Hospital
         Medicine.
         Comanagement relationships can be fraught with ambiguity, so he offered the following “existential questions”
          to ask in an effort to achieve clarity:
         ▸Why are we being asked to comanage this patient's care?
         ▸What are the “rules of engagement”? Do I make suggestions or decisions?
         ▸What responsibilities are mine vs. yours?
         ▸Where do our responsibilities overlap, and how do we manage those overlaps?
         ▸What happens if we disagree?
         ▸Who makes the final call?

         “If you haven't at least thought these through and talked these over with the people with whom you're working,
         you're setting yourself up for a problem, a conflict at some point down the road,” Dr. Siegal warned.
         In terms of protocol, “you absolutely have to insist on uniformity,” said Dr. Siegal, a hospitalist who is
         regional medical director of Cogent Healthcare, Nashville, Tenn.
         Don't have a two-tiered system “because nothing drives specialists
         and nurses more crazy than to see one hospitalist come in and do one thing and then see the next hospitalist
         either unable to do it or do it radically differently.”
         If you need help defining a reasonable role for a hospitalist, Dr. Siegal recommended reviewing the core
         competencies published in the January/February 2006 supplement of the Journal of Hospital Medicine
         (www3.interscience.wiley.com/journal/112396185/issue
         Dr. Siegal recommends negotiating your expectations with other members of the comanagement team and
         developing guidelines when ambiguity exists. When he was director of the hospitalist program at
         Meriter Hospital, an affiliate of the University of Wisconsin, Madison, he sat down with cardiologists
         at the hospital and devised cardiology admission guidelines so everyone would be on the same page. 
         They agreed that the cardiologist would admit patients with specific conditions that included 
         ST-segment elevation, myocardial infarction, and advanced heart block requiring or potentially 
         requiring emergency temporary pacing, while the hospitalist would admit patients with a different 
         set of conditions that included chest pain of uncertain etiology and atrial arrhythmias.
         “Does this cover every possible permutation? No,” Dr. Siegal said. “But the point was, we agreed 
         on a basic set of rules up front. We disseminated them, put them in the emergency department, 
         and it lowered the number of confusing calls and decreased the amount of angst. It's worked really nicely. 
         As much as you can, cookbook this stuff up front so you know what the rules are.”
         Revisiting the comanagement relationship after the first few months is a good idea, he noted, 
         “because perspectives change, sometimes for the better, and sometimes for the worse.” 
         As a case in point he described a surgeon he worked with who was initially skeptical of hospitalists. 
         One day Dr. Siegal was called to stabilize one of the surgeon's patients who was crashing 
         in the postanesthesia care unit. The surgeon was busy with a case at another hospital when this occurred.
         “I took care of that patient and the next thing I knew, I could do no wrong,” Dr. Siegal recalled. 
         '''
        entities = self.extractor.extract(text)
        assert entities == [Concept("myocardial infarction", "DISEASE"), Concept("heart block", "DISEASE"),
                            Concept("chest pain", "DISEASE"), Concept("atrial arrhythmias", "DISEASE")]
