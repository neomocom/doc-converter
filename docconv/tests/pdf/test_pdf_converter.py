import os
import datetime

import pytest
from pdf import Pdf2TextConverter
from pdf import PdfConversionError

pdf2_text_converter = Pdf2TextConverter()


def test_pdf():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'test.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author == 'BMC - ITS'
        assert text_result.creation_date == datetime.datetime(2014,11, 7, 20, 16, 50)
        assert text_result.title == ''
        assert text_result.text.startswith("The 8P")
        assert "Problems with medications                      □   Medication specific" in text_result.text
        assert text_result.text.endswith("available to the patient")


def test_pdf_with_title():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'test_with_title.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author == 'BMC - ITS'
        assert text_result.creation_date == datetime.datetime(2009, 11, 9, 16, 3, 25)
        assert text_result.title == 'Patient PASS'
        assert text_result.text.startswith("Patient PASS: A Transition Record")
        assert """If I have the following problems …       I should …                              Important contact information:
  1. _________________________              1. _________________________            1. My primary """ in text_result.text


def test_pdf_with_multi_pages():
    pdf = os.path.join(os.path.dirname(__file__), 'resources', 'multi_page.pdf')
    with open(pdf, "rb") as f:
        text_result = pdf2_text_converter.to_text(f.read())
        assert text_result.author == 'Lisa Zoks'
        assert text_result.creation_date == datetime.datetime(2020, 10, 5, 19, 25, 22)
        assert text_result.title == ''
        assert text_result.text.startswith("October 5, 2020\n\n\n")
        assert "Dear Administrator Verma," in text_result.text
        assert "Hospital Policy” (https://www.oig.hhs.gov/oei/reports/oei-02-15-00020.pdf)," in text_result.text
        assert """The primary reason data transparency is necessary is that we are concerned that elimination of the
inpatient-only list could have the unintended consequence of increasing out-of-pocket costs for
Medicare beneficiaries. For example""" in text_result.text

        assert text_result.text.endswith("President, Society of Hospital Medicine")


def test_pdf_errors_are_caught():
        with pytest.raises(PdfConversionError) as ex:
            pdf2_text_converter.to_text("not bytes")
        assert str(ex.value) == 'Error occurred while loading pdf document (TypeError)'