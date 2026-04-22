from io import BytesIO

from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.pipeline_options import TableStructureOptions, TableFormerMode, PdfPipelineOptions, \
    EasyOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.io import DocumentStream


class Pdf2TextConverter:

    def __init__(self, do_ocr=False):
        pipeline_options = PdfPipelineOptions(
            do_ocr=do_ocr,
            ocr_options=EasyOcrOptions(force_full_page_ocr=False),
            force_backend_text=False,
            do_code_enrichment=False,
            do_formula_enrichment=False,
            do_table_structure=True,
            table_structure_options=TableStructureOptions(
                do_cell_matching=True, mode=TableFormerMode.ACCURATE
            )
        )
        self.converter = DocumentConverter(
            format_options={
                "pdf": PdfFormatOption(
                    pipeline_options=pipeline_options,
                    backend=PyPdfiumDocumentBackend,  # With the standard backend words are awkwardly split
                )
            }
        )

    @staticmethod
    def to_text(pdf_content):
        return Pdf2TextConverter().convert_to_text(pdf_content)

    def convert_to_text(self, pdf_content):
        try:
            result = self.converter.convert(
                DocumentStream(name="no_name", stream=BytesIO(pdf_content))
            )
            doc = result.document
            return PdfResult(doc.export_to_text().strip(),
                             doc.export_to_markdown(),
                             author=None,
                             creation_date=None,
                             title=None
                             )
        except Exception as ex:
            raise PdfConversionError("Error occurred while converting pdf document (%s)" % str(ex.__class__.__name__))


class PdfResult:

    def __init__(self, text, markdown, author=None, creation_date=None, title=None):
        self.text = text
        self.markdown = markdown
        self.author = author
        self.creation_date = creation_date
        self.title = title


class PdfConversionError(Exception):
    pass
