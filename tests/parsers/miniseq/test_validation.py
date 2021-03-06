import unittest
from unittest.mock import patch
from csv import reader
from io import StringIO

from parsers.miniseq.validation import validate_sample_sheet
from parsers.exceptions import SampleSheetError


class TestValidation(unittest.TestCase):
    """
    Tests valid and invalid sample sheets
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("parsers.miniseq.validation.get_csv_reader")
    def test_validate_sample_sheet_no_header(self, mock_csv_reader):
        """
        Given a sample sheet with no header, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        headers = ("Sample_ID,Sample_Name," +
                   "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project")

        field_values = (
                "15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n" +
                "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n" +
                "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        reads = (
                "151\n" +
                "151\n"
        )

        file_contents_str = (
                "[Reads]\n" +
                "{reads}\n" +
                "[Data]\n" +
                "{headers}\n" +
                "{field_values}"
        ).format(headers=headers, reads=reads, field_values=field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be an invalid sample sheet
        self.assertFalse(res.is_valid())
        # Only should have 1 error
        self.assertEqual(len(res.error_list), 1)
        # Error type should be SampleSheetError
        self.assertEqual(type(res.error_list[0]), SampleSheetError)

    @patch("parsers.miniseq.validation.get_csv_reader")
    def test_validate_sample_sheet_no_data(self, mock_csv_reader):
        """
        Given a sample sheet with no data, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        field_values = (
                "15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n" +
                "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n" +
                "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n" +
                "Local Run Manager, 4004\n" +
                "Experiment Name, Some_Test_Data\n" +
                "Date, 2015-05-14\n" +
                "Workflow, GenerateFastQWorkflow\n" +
                "Description, 12-34\n" +
                "Chemistry, Yes\n"
        )

        reads = (
                "151\n" +
                "151\n"
        )

        file_contents_str = (
                "[Header]\n" +
                "{field_values}\n" +
                "[Reads]\n" +
                "{reads}"
        ).format(field_values=field_values, reads=reads)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be an invalid sample sheet
        self.assertFalse(res.is_valid())
        # Only should have 2 error
        self.assertEqual(len(res.error_list), 2)
        # Error type should be SampleSheetError
        self.assertEqual(type(res.error_list[0]), SampleSheetError)
        self.assertEqual(type(res.error_list[1]), SampleSheetError)

    @patch("parsers.miniseq.validation.get_csv_reader")
    def test_validate_sample_sheet_missing_data_header(self, mock_csv_reader):
        """
        Given a sample sheet with no data header, make sure the correct errors are included in the response
        :param mock_csv_reader:
        :return:
        """
        h_field_values = (
                "Local Run Manager Analysis Id, 4004\n" +
                "Experiment Name, Some_Test_Data\n" +
                "Date, 2015-05-14\n" +
                "Workflow, GenerateFastQWorkflow\n" +
                "Description, 12-34\n" +
                "Chemistry, Yes\n"
        )

        reads = (
                "151\n" +
                "151\n"
        )

        d_headers = ("Sample_Name," +
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,")

        d_field_values = (
                "15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n" +
                "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n" +
                "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        file_contents_str = (
                "[Header]\n" +
                "{h_field_values}\n" +
                "[Reads]\n" +
                "{reads}\n" +
                "[Data]\n" +
                "{d_headers}\n" +
                "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be an invalid sample sheet
        self.assertFalse(res.is_valid())
        # Only should have 1 error
        self.assertEqual(len(res.error_list), 1)
        # Error type should be SampleSheetError
        self.assertEqual(type(res.error_list[0]), SampleSheetError)

    @patch("parsers.miniseq.validation.get_csv_reader")
    def test_validate_sample_sheet_valid(self, mock_csv_reader):
        """
        Given a valid sample sheet, test that everything shows as valid
        :param mock_csv_reader:
        :return:
        """
        h_field_values = (
                "Local Run Manager Analysis Id, 4004\n" +
                "Experiment Name, Some_Test_Data\n" +
                "Date, 2015-05-14\n" +
                "Workflow, GenerateFastQWorkflow\n" +
                "Description, 12-34\n" +
                "Chemistry, Yes\n"
        )

        reads = (
                "151\n" +
                "151\n"
        )

        d_headers = ("Sample_ID,Sample_Name," +
                     "I7_Index_ID,index,I5_Index_ID,index2,Sample_Project,")

        d_field_values = (
                "15-0318-4004,15-0318,N701,TAAGGCGA,S502,CTCTCTAT,203\n" +
                "15-0455-4004,15-0455,N701,TAAGGCGA,S503,TATCCTCT,203\n" +
                "15-0462-4004,15-0462,N701,TAAGGCGA,S505,GTAAGGAG,203\n"
        )

        file_contents_str = (
                "[Header]\n" +
                "{h_field_values}\n" +
                "[Reads]\n" +
                "{reads}\n" +
                "[Data]\n" +
                "{d_headers}\n" +
                "{d_field_values}"
        ).format(h_field_values=h_field_values, reads=reads, d_headers=d_headers, d_field_values=d_field_values)

        # converts string as a pseudo file / memory file
        sample_sheet_file = StringIO(file_contents_str)

        # the call to get_csv_reader() inside parse_samples() will return
        # items inside side_effect
        mock_csv_reader.side_effect = [reader(sample_sheet_file)]

        res = validate_sample_sheet(None)

        # This should be a valid sample sheet
        self.assertTrue(res.is_valid())
