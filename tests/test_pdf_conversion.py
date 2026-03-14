import os
import sys

import edq.util.dirent

import quizcomp.latex
import quizcomp.pdf
import tests.base

MIN_PDF_SIZE_BYTES = 1000

class PDFConversionTest(tests.base.BaseTest):
    """
    Test PDF generation for quizzes in 'tests/quizzes/good' directory.
    Tests cover both local and Docker-based PDF generation.
    """

    pass

def _add_pdf_tests():
    quiz_files = tests.base.discover_good_quiz_files()
    if (not quiz_files):
        raise ValueError("No quiz.json files found in '%s' or its subdirectories." % (tests.base.GOOD_QUIZZES_DIR))

    for quiz_path in quiz_files:
        _add_pdf_test(quiz_path)

def _add_pdf_test(path):
    base_test_name = os.path.basename(os.path.dirname(path))

    # Test local PDF generation.
    test_name = "test_quiz_pdf_local_%s" % (base_test_name)
    setattr(PDFConversionTest, test_name, _get_quiz_pdf_local_test_method(path))

    # Test Docker PDF generation.
    test_name = "test_quiz_pdf_docker_%s" % (base_test_name)
    setattr(PDFConversionTest, test_name, _get_quiz_pdf_docker_test_method(path))

def _get_quiz_pdf_local_test_method(path):
    """
    Get a test for generating a PDF locally.
    """

    def __method(self):
        _run_pdf_test(self, path, use_docker = False)

    return __method

def _get_quiz_pdf_docker_test_method(path):
    """
    Get a test for generating a PDF with Docker.
    """

    def __method(self):
        _run_pdf_test(self, path, use_docker = True)

    return __method

def _run_pdf_test(self, path, use_docker = False):
    if (use_docker and sys.platform.startswith("win")):
        self.skipTest('Skipping Docker tests on Windows.')

    quizcomp.latex.set_pdflatex_use_docker(use_docker)

    if (not quizcomp.latex.is_available()):
        self.skipTest("`pdflatex` is not available.")

    temp_dir = edq.util.dirent.get_temp_dir(prefix = "quizcomp_pdf_test_")
    quiz, variants, _ = quizcomp.pdf.make_with_path(path, base_out_dir = temp_dir)

    for variant in variants:
        pdf_file = os.path.join(temp_dir, quiz.title, f"{variant.title}.pdf")
        self.assertTrue(os.path.exists(pdf_file), f"PDF '{pdf_file}' not generated.")
        self.assertTrue(os.path.getsize(pdf_file) > MIN_PDF_SIZE_BYTES, f"PDF '{pdf_file}' is too small.")

_add_pdf_tests()
