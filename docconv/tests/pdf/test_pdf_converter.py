import os

import pytest
from pdf import Pdf2TextConverter
from pdf import PdfConversionError

pdf2_text_converter = Pdf2TextConverter()


def test_pdf():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'test.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author is None
        assert text_result.creation_date is None
        assert text_result.title is None
        assert text_result.text.startswith("The 8P Screening Tool Identifying Your Patient's Risk for Adverse Events "
                                           "After Discharge\n\n")
        assert "Problems with medications" in text_result.text
        assert text_result.text.endswith("available to the patient")
        assert text_result.markdown.startswith("<!-- image -->\n\n## The 8P Screening Tool Identifying Your "
                                               "Patient's Risk for Adverse Events After Discharge\n\n")
        assert text_result.markdown.endswith("available to the patient")


def test_pdf_with_title():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'test_with_title.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author is None
        assert text_result.creation_date is None
        assert text_result.title is None
        assert text_result.text.startswith("Patient PASS: A Transition Record")
        assert "If I have the following problems …\n" in text_result.text
        assert "\n1. My primary doctor:" in text_result.text
        assert text_result.markdown.startswith("<!-- image -->\n\n## Patient PASS: A Transition Record")


def test_pdf_with_multi_pages():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'multi_page.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author is None
        assert text_result.creation_date is None
        assert text_result.title is None
        assert text_result.text.startswith("October 5, 2020\n\n")
        assert "Dear Administrator Verma," in text_result.text
        assert 'Hospital Policy" (https://www.oig.hhs.gov/oei/reports/oei-02-15-00020.pdf),' in text_result.text
        assert "The primary reason data transparency is necessary is that we are concerned that " in text_result.text
        assert text_result.text.endswith("President, Society of Hospital Medicine")
        assert text_result.markdown.endswith("President, Society of Hospital Medicine")


def test_pdf_errors_are_caught():
    with pytest.raises(PdfConversionError) as ex:
        pdf2_text_converter.to_text("not bytes")
    assert str(ex.value) == 'Error occurred while converting pdf document (TypeError)'


def test_pdf_text_layer_extracted_without_ocr():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'leitungswasserschaden_text.pdf')
    with open(pdf, "rb") as f:
        text_result = Pdf2TextConverter().convert_to_text(f.read())
        assert text_result.text.startswith("LEITUNGSWASSERSCHADEN\n\nAlles steht unter Wasser")
        assert "- › Bitte bewahren Sie Ruhe.\n" in text_result.text


def test_pdf_image_not_extracted_without_ocr():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'leitungswasserschaden_image.pdf')
    with open(pdf, "rb") as f:
        text_result = Pdf2TextConverter(do_ocr=False).convert_to_text(f.read())
        assert "Wasser" not in text_result.text
        assert "Zuallererst" not in text_result.text


def test_pdf_image_extracted_with_ocr():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'leitungswasserschaden_image.pdf')
    with open(pdf, "rb") as f:
        text_result = Pdf2TextConverter(do_ocr=True).convert_to_text(f.read())
        assert text_result.text.startswith("Zuallererst heißt es: Gefahren minimieren! Schützen Sie sich selbst."
                                           "\n\n- Bitte bewahren Sie Ruhe.\n")
