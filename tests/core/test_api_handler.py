import unittest
from unittest.mock import patch
from os import path

from core import api_handler

from parsers.miseq.parser import Parser
from api.exceptions import IridaResourceError
from model.exceptions import ModelValidationError

path_to_module = path.abspath(path.dirname(__file__))
if len(path_to_module) == 0:
    path_to_module = '.'


class TestPrepareAndValidateForUpload(unittest.TestCase):
    """
    Tests the core.api_handler.prepare_and_validate_for_upload function
    """

    sequencing_run = None

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

        # make a sequencing run that we can work with in the tests
        sheet_file = path.join(path_to_module, "fake_ngs_data", "SampleSheet.csv")
        global sequencing_run
        sequencing_run = Parser.get_sequencing_run(sheet_file)

    def tearDown(self):
        # set out sequencing run back to None so each tests starts from a clean state
        global sequencing_run
        sequencing_run = None

    @patch("core.api_handler._get_api_instance")
    def test_valid_all_functions_called(self, mock_api_instance):
        """
        Makes sure that all functions are called when a valid sequencing run in given
        :return:
        """
        global sequencing_run

        # create mocked data for each call that will occur
        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.project_exists.side_effect = [True]
        stub_api_instance.sample_exists.side_effect = [True, True, True]

        mock_api_instance.side_effect = [stub_api_instance]

        # check that each function was called the correct number of times and with the correct data
        res = api_handler.prepare_and_validate_for_upload(sequencing_run)
        stub_api_instance.project_exists.assert_called_once_with("6")
        stub_api_instance.sample_exists.assert_has_calls([
            unittest.mock.call('01-1111', '6'),
            unittest.mock.call('02-2222', '6'),
            unittest.mock.call('03-3333', '6')
        ])
        self.assertTrue(res.is_valid())

    @patch("core.api_handler._get_api_instance")
    def test_invalid_validation_project_does_not_exist(self, mock_api_instance):
        """
        Makes sure the returned validation result includes all types of invalid properties in the sequencing run
        Project does not exist on IRIDA
        :return:
        """
        global sequencing_run

        # create mock data for a non existant project
        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.project_exists.side_effect = [False]

        mock_api_instance.side_effect = [stub_api_instance]

        # verify the functions are called correctly
        res = api_handler.prepare_and_validate_for_upload(sequencing_run)
        stub_api_instance.project_exists.assert_called_once_with("6")

        # the result should be invalid with an IridaResourceError
        self.assertFalse(res.is_valid())
        self.assertEqual(res.error_count(), 1)
        self.assertEqual(type(res.error_list[0]), IridaResourceError)

    @patch("core.api_handler._get_api_instance")
    def test_valid_send_sample(self, mock_api_instance):
        """
        Makes sure we try to send a sample to IRIDA if it doesn't exist
        :return:
        """
        global sequencing_run

        # create mocks for each function call that will occur
        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.project_exists.side_effect = [True]
        stub_api_instance.sample_exists.side_effect = [True, True, False, True]
        stub_api_instance.send_sample.side_effect = [True]

        mock_api_instance.side_effect = [stub_api_instance]

        res = api_handler.prepare_and_validate_for_upload(sequencing_run)

        # Ensure we check the existence of the sample after uploading it
        stub_api_instance.sample_exists.assert_has_calls([
            unittest.mock.call('01-1111', '6'),
            unittest.mock.call('02-2222', '6'),
            unittest.mock.call('03-3333', '6'),
            unittest.mock.call('03-3333', '6'),
        ])

        self.assertTrue(res.is_valid())

    @patch("core.api_handler._get_api_instance")
    def test_invalid_could_not_send_sample(self, mock_api_instance):
        """
        Makes sure we try to send a sample to IRIDA if it doesn't exist,
            and IridaResourceError is thrown when it cannot send the sample
        :return:
        """
        global sequencing_run

        # create mocks for each function call that will occur
        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.project_exists.side_effect = [True]
        stub_api_instance.sample_exists.side_effect = [True, True, False, False]
        stub_api_instance.send_sample.side_effect = [True]

        mock_api_instance.side_effect = [stub_api_instance]

        res = api_handler.prepare_and_validate_for_upload(sequencing_run)

        # Ensure we check the existence of the sample after uploading it
        stub_api_instance.sample_exists.assert_has_calls([
            unittest.mock.call('01-1111', '6'),
            unittest.mock.call('02-2222', '6'),
            unittest.mock.call('03-3333', '6'),
            unittest.mock.call('03-3333', '6'),
        ])

        # check that it's invalid and the correct error is included
        self.assertFalse(res.is_valid())
        self.assertEqual(res.error_count(), 1)
        self.assertEqual(type(res.error_list[0]), IridaResourceError)


class TestUploadSequencingRun(unittest.TestCase):
    """
    Tests the core.api_handler.upload_sequencing_run function
    """

    sequencing_run = None

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)
        # make a sequencing run that we can work with in the tests
        sheet_file = path.join(path_to_module, "fake_ngs_data", "SampleSheet.csv")
        global sequencing_run
        sequencing_run = Parser.get_sequencing_run(sheet_file)

    def tearDown(self):
        # reset out make sequencing run back to None so all tests start from clean
        global sequencing_run
        sequencing_run = None

    @patch("core.api_handler._get_api_instance")
    def test_valid_all_functions_called(self, mock_api_instance):
        """
        Makes sure that all functions are called when a valid sequencing run in given
        :return:
        """
        global sequencing_run

        # set up all the mock data for a fake upload
        for samp in sequencing_run.project_list[0].sample_list:
            samp.sequence_file = "mock_sample"

        mock_sequence_run_id = 55

        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.create_seq_run.side_effect = [mock_sequence_run_id]
        stub_api_instance.set_seq_run_uploading.side_effect = [True]
        stub_api_instance.send_sequence_files.side_effect = [True, True, True]
        stub_api_instance.set_seq_run_complete.side_effect = [True]

        mock_api_instance.side_effect = [stub_api_instance]

        api_handler.upload_sequencing_run(sequencing_run)

        # ensure the response matches our mocks, and that all the needed functions were called correctly
        stub_api_instance.create_seq_run.assert_called_once_with(sequencing_run.metadata)
        stub_api_instance.set_seq_run_uploading.assert_called_once_with(mock_sequence_run_id)
        stub_api_instance.send_sequence_files.assert_has_calls([
            unittest.mock.call(project_id='6', sample_name='01-1111', sequence_file='mock_sample', upload_id=55),
            unittest.mock.call(project_id='6', sample_name='02-2222', sequence_file='mock_sample', upload_id=55),
            unittest.mock.call(project_id='6', sample_name='03-3333', sequence_file='mock_sample', upload_id=55)
        ])
        stub_api_instance.set_seq_run_complete.assert_called_once_with(mock_sequence_run_id)

    @patch("core.api_handler._get_api_instance")
    def test_invalid_error_raised(self, mock_api_instance):
        """
        Makes sure that the sequencing run is set to error when an exception is thrown
        :return:
        """
        global sequencing_run

        # create mock data for our invalid sequencing run
        for samp in sequencing_run.project_list[0].sample_list:
            samp.sequence_file = "mock_sample"

        mock_sequence_run_id = 55

        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.create_seq_run.side_effect = [mock_sequence_run_id]
        stub_api_instance.set_seq_run_uploading.side_effect = IridaResourceError("Boom")
        stub_api_instance.set_seq_run_error.side_effect = [True]

        mock_api_instance.side_effect = [stub_api_instance]

        # make sure the IridaResourceError was thrown correctly
        with self.assertRaises(IridaResourceError):
            api_handler.upload_sequencing_run(sequencing_run)

        # verify the sequencing run was set to an error state after the upload was run
        stub_api_instance.create_seq_run.assert_called_once_with(sequencing_run.metadata)
        stub_api_instance.set_seq_run_uploading.assert_called_once_with(mock_sequence_run_id)
        stub_api_instance.set_seq_run_error.assert_called_once_with(mock_sequence_run_id)


class TestSendProject(unittest.TestCase):
    """
    Tests the core.api_handler.test_send_project function
    """

    def setUp(self):
        print("\nStarting " + self.__module__ + ": " + self._testMethodName)

    @patch("core.api_handler.model_validator")
    @patch("core.api_handler._get_api_instance")
    def test_all_functions_called(self, mock_api_instance, mock_model_validator):
        """
        Makes sure that all relevant functions are called when sending a project
        :return:
        """

        # mock data for sending a project
        mock_project = "mock_project"

        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.send_project.side_effect = [True]

        mock_api_instance.side_effect = [stub_api_instance]

        mock_model_validator.validate_send_project.side_effect = [True]

        # send the mock project
        api_handler.send_project(mock_project)

        # check that all the key functions are called with the mock data given
        stub_api_instance.send_project.assert_called_once_with(mock_project)
        mock_model_validator.validate_send_project.assert_called_once_with(mock_project)

    @patch("core.api_handler.model_validator")
    @patch("core.api_handler._get_api_instance")
    def test_can_not_send_project(self, mock_api_instance, mock_model_validator):
        """
        Makes sure that an IridaResourceError is thrown when the api is unable to upload
            (IridaResourceError) when uploading a project
        :return:
        """

        mock_project = "mock_project"

        stub_api_instance = unittest.mock.MagicMock()
        stub_api_instance.send_project.side_effect = IridaResourceError("BOOM")

        mock_api_instance.side_effect = [stub_api_instance]

        mock_model_validator.validate_send_project.side_effect = [True]

        with self.assertRaises(IridaResourceError):
            api_handler.send_project(mock_project)

        mock_model_validator.validate_send_project.assert_called_once_with(mock_project)

    @patch("core.api_handler.model_validator")
    @patch("core.api_handler._get_api_instance")
    def test_project_invalid(self, mock_api_instance, mock_model_validator):
        """
        Makes sure that an IridaResourceError is thrown when an invalid project is
            given (ModelValidationError) when uploading a project
        :return:
        """

        mock_project = "mock_project"

        stub_api_instance = unittest.mock.MagicMock()
        mock_api_instance.side_effect = [stub_api_instance]

        mock_model_validator.validate_send_project.side_effect = ModelValidationError("BOOM", None)

        with self.assertRaises(IridaResourceError):
            api_handler.send_project(mock_project)
