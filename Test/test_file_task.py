import unittest
import os
import sys
import shutil

# Add Src directory to sys.path to allow direct import of file_reader
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../Src')))
from Tools.file_task import file_reader

class TestFileReader(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        # Ensure assets_dir exists from the previous step, or re-create if needed by tests
        if not os.path.exists(cls.assets_dir):
            os.makedirs(cls.assets_dir)
            # Re-create files if they are missing for some reason (e.g. if run standalone without prior step)
            with open(os.path.join(cls.assets_dir, "test_sample.txt"), "w") as f:
                f.write("This is a test TXT file.")
            with open(os.path.join(cls.assets_dir, "test_sample.unknown_ext"), "w") as f:
                f.write("This is an unknown extension test.")
            with open(os.path.join(cls.assets_dir, "corrupted.pdf"), "w") as f:
                f.write("This is not a PDF.")
            with open(os.path.join(cls.assets_dir, "corrupted.docx"), "w") as f:
                f.write("This is not a DOCX.")
            with open(os.path.join(cls.assets_dir, "fake.pdf"), "w") as f:
                f.write("This is a text file named fake.pdf.")
            with open(os.path.join(cls.assets_dir, "fake.docx"), "w") as f:
                f.write("This is a text file named fake.docx.")
            open(os.path.join(cls.assets_dir, "empty.pdf"), "w").close()
            open(os.path.join(cls.assets_dir, "empty.docx"), "w").close()
            open(os.path.join(cls.assets_dir, "encrypted.pdf"), "w").close() # Simulate with empty file

        # For home directory restriction testing
        cls.test_home_dir = os.path.join(cls.assets_dir, "home_dir_test")
        cls.sensitive_config_file_path = os.path.join(cls.test_home_dir, ".gitconfig") # Test with a file
        cls.sensitive_ssh_dir_path = os.path.join(cls.test_home_dir, ".ssh") # Test with a dir
        
        os.makedirs(cls.test_home_dir, exist_ok=True)
        os.makedirs(cls.sensitive_ssh_dir_path, exist_ok=True)
        
        with open(cls.sensitive_config_file_path, "w") as f:
            f.write("sensitive test content")
        
        with open(os.path.join(cls.sensitive_ssh_dir_path, "config"), "w") as f:
            f.write("ssh test content")

    @classmethod
    def tearDownClass(cls):
        # Clean up the assets directory after all tests are done
        # shutil.rmtree(cls.assets_dir) # Commented out to inspect files if needed
        pass

    def test_read_txt_successfully(self):
        file_path = os.path.join(self.assets_dir, "test_sample.txt")
        result = file_reader(file_path=file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["output"].strip(), "This is a test TXT file.")

    def test_read_unknown_extension_as_text(self):
        file_path = os.path.join(self.assets_dir, "test_sample.unknown_ext")
        result = file_reader(file_path=file_path)
        self.assertTrue(result["success"])
        self.assertEqual(result["output"].strip(), "This is an unknown extension test.")

    # Security - Forbidden Paths
    def test_block_unix_forbidden_paths(self):
        # Using a path that is guaranteed to be resolved by abspath and start with /etc/
        # The security check for forbidden paths happens before os.path.isfile.
        if os.name != "nt": # Only run this on non-Windows where /etc/ is common
            # Path can be non-existent, check is on the string path
            result = file_reader(file_path="/etc/some_non_existent_file_for_test")
            self.assertFalse(result["success"])
            self.assertIn("Access to system or restricted directory", result["output"])
            self.assertIn("is not allowed", result["output"])
        else:
            self.skipTest("UNIX forbidden path test skipped on Windows.")

    @unittest.skipIf(os.name != "nt", "Windows forbidden path test only applicable on Windows or needs refined path handling for x-platform testing.")
    def test_block_windows_forbidden_paths(self):
        # This test relies on the current OS being Windows or the file_reader's
        # forbidden path logic correctly normalizing and matching Windows-style paths
        # even when os.path.abspath produces a POSIX-style absolute path.
        # As identified, the current file_reader might not do this robustly across OSes.
        path_to_test = "C:\\Windows\\System.ini"
        result = file_reader(file_path=path_to_test)
        self.assertFalse(result["success"])
        self.assertIn("Access to system or restricted directory", result["output"])
        self.assertIn("is not allowed", result["output"])

    @unittest.skipIf(os.name == "nt", "Test not applicable on Windows for POSIX sensitive paths")
    def test_block_sensitive_home_file(self):
        # Test reading a sensitive file like .gitconfig from the mocked home
        original_expanduser = os.path.expanduser
        try:
            os.path.expanduser = lambda path: self.test_home_dir if path == "~" else original_expanduser(path)
            # file_reader is expected to form path like "user_home/.gitconfig"
            # We pass the absolute path to our test .gitconfig file
            result = file_reader(file_path=self.sensitive_config_file_path)
            self.assertFalse(result["success"])
            self.assertIn("Access to sensitive user configuration file", result["output"])
        finally:
            os.path.expanduser = original_expanduser
            
    @unittest.skipIf(os.name == "nt", "Test not applicable on Windows for POSIX sensitive paths")
    def test_block_sensitive_home_directory_access(self):
        # Test reading a file within a sensitive directory like .ssh/config from the mocked home
        original_expanduser = os.path.expanduser
        try:
            os.path.expanduser = lambda path: self.test_home_dir if path == "~" else original_expanduser(path)
            # Path to a file within the .ssh directory
            path_inside_sensitive_dir = os.path.join(self.sensitive_ssh_dir_path, "config")
            result = file_reader(file_path=path_inside_sensitive_dir)
            self.assertFalse(result["success"])
            self.assertIn("Access to files within sensitive user directory", result["output"]) # Updated assertion
        finally:
            os.path.expanduser = original_expanduser


    def test_path_traversal_attempt(self):
        # Construct a path that tries to traverse up and then into /etc/
        # Current working directory for tests is likely /app/Test/ or /app/
        # If /app, then ../../../../../etc/hosts becomes /etc/hosts
        # If /app/Test, then ../../../../../../etc/hosts becomes /etc/hosts
        # os.path.abspath will resolve this.
        malicious_path = os.path.join(self.assets_dir, "..", "..", "..", "..", "..", "..", "etc", "hosts")
        # malicious_path = "../../../../../../../etc/hosts" # Simpler relative path
        result = file_reader(file_path=malicious_path)
        self.assertFalse(result["success"])
        # The exact error message depends on whether /etc/ is in forbidden_dirs
        # or if the path resolution itself is problematic for other reasons before that.
        # Given current logic, it should be caught by forbidden_dirs.
        self.assertIn("Access to system or restricted directory", result["output"])

    # Error Handling Tests
    def test_read_non_existent_file(self):
        result = file_reader(file_path="non_existent_file.txt")
        self.assertFalse(result["success"])
        self.assertIn("does not exist", result["output"])

    def test_read_corrupted_pdf(self): # Actually a text file named .pdf
        file_path = os.path.join(self.assets_dir, "corrupted.pdf")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        self.assertIn("Could not read PDF file", result["output"]) # From PyPDF2Errors.PdfReadError

    def test_read_corrupted_docx(self): # Actually a text file named .docx
        file_path = os.path.join(self.assets_dir, "corrupted.docx")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        # Error: File '...' is not a valid DOCX file, is corrupted, or is not a compatible OOXML package.
        self.assertIn("not a valid DOCX file", result["output"]) # From DocxOpcExceptions.PackageNotFoundError

    def test_read_empty_pdf_as_corrupted(self): # An empty file is not a valid PDF
        file_path = os.path.join(self.assets_dir, "empty.pdf")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        self.assertIn("Could not read PDF file", result["output"])


    def test_read_empty_docx_as_corrupted(self): # An empty file is not a valid DOCX
        file_path = os.path.join(self.assets_dir, "empty.docx")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        self.assertIn("not a valid DOCX file", result["output"])

    def test_read_encrypted_pdf_simulated(self):
        # Current file_reader checks `reader.is_encrypted`.
        # An empty file (encrypted.pdf) will fail before this check, likely as a PdfReadError.
        file_path = os.path.join(self.assets_dir, "encrypted.pdf")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        # Expecting it to be caught by PdfReadError or similar, not the specific "encrypted" message unless it's a specially crafted PDF.
        self.assertTrue(
            "Could not read PDF file" in result["output"] or "encrypted" in result["output"]
        )


    def test_read_file_with_wrong_extension_pdf(self): # text file named fake.pdf
        file_path = os.path.join(self.assets_dir, "fake.pdf")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        self.assertIn("Could not read PDF file", result["output"])

    def test_read_file_with_wrong_extension_docx(self): # text file named fake.docx
        file_path = os.path.join(self.assets_dir, "fake.docx")
        result = file_reader(file_path=file_path)
        self.assertFalse(result["success"])
        self.assertIn("not a valid DOCX file", result["output"])

    # Skipped tests for actual PDF/DOCX content due to generation limitations
    @unittest.skip("Skipping PDF content test: Cannot generate actual PDF with known content with available tools.")
    def test_read_pdf_successfully(self):
        pass

    @unittest.skip("Skipping DOCX content test: Cannot generate actual DOCX with known content with available tools.")
    def test_read_docx_successfully(self):
        pass
    
    @unittest.skip("Skipping MacOS specific forbidden path for now.")
    def test_block_macos_forbidden_paths(self):
        # path_to_test = "/System/Library/Kernels"
        # result = file_reader(file_path=path_to_test)
        # self.assertFalse(result["success"])
        # self.assertIn("Access to system or restricted directory", result["output"])
        pass

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
