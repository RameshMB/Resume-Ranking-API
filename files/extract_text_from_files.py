from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import io
import docx2txt


def extract_text_from_pdf_file(pdf_path):
    pdf_text = ''
    with open(pdf_path, 'rb') as fh:
        # iterate over all pages of PDF document
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            # creating a resource manager
            resource_manager = PDFResourceManager()

            # create a file handle
            fake_file_handle = io.StringIO()

            # creating a text converter object
            converter = TextConverter(
                resource_manager,
                fake_file_handle,
                codec='utf-8',
                laparams=LAParams()
            )

            # creating a page interpreter
            page_interpreter = PDFPageInterpreter(
                resource_manager,
                converter
            )
            # process current page
            page_interpreter.process_page(page)

            # extract text
            text = fake_file_handle.getvalue()
            pdf_text += ' ' + text
            # close open handles
        converter.close()
        fake_file_handle.close()
    return pdf_text


def get_text_from_docx_file(filename):
    doc_text = docx2txt.process(filename)
    return doc_text


def get_text_from_text_file(filename):
    with open(filename, "r") as file:
        text_data = file.read()
    return text_data
