import os
import stat
import unittest
from pathlib import PurePath
from configparser import MissingSectionHeaderError

from src.app_config import ConfigHandler
from src.app_config import AccessConfigError
from src.app_config import BackupConfigError
from src.app_config import RebuildConfigError
from src.app_config import NameConfigError
from src.app_config import CopyConfigError


class TestConfigHandler(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass

    def setUp(self) -> None:
        self.example_config = 'example_config.ini'
        self.config_name = 'config.ini'
        self.fixtures = 'tests/fixtures'
        self.test = ConfigHandler()

    def tearDown(self) -> None:
        del self.example_config
        del self.config_name
        del self.fixtures
        del self.test

    def test_set_configparser(self):
        self.test._set_configparser(name=self.config_name,
                                    directory=None)
        result = self.test._config.sections()
        self.assertEqual(result[0], "MQTT")
        self.assertEqual(result[1], "CORE")
        self.assertEqual(result[2], "LOG")

    def test__str__(self):
        self.assertRegex(str(self.test),
                         'Config:')

    def test__repr__(self):
        result = repr(self.test)
        self.assertRegex(result,
                         "ConfigHandler")
        self.assertRegex(result,
                         self.config_name)

    def test_copy_string(self):
        source = self.test._search_config(name=self.example_config,
                                          directory=None)
        destination = self.test._search_config(name=self.config_name,
                                               directory=self.fixtures)
        result = self.test._copy_string(src=source,
                                        dst=destination)
        self.assertEqual(result, "Copied string success")

    def test_wrong_copy_string(self):
        source = self.test._search_config(name=self.example_config,
                                          directory=None)
        destination = self.test._search_config(name=self.config_name,
                                               directory=self.fixtures)
        # Change mode to not read, not write, not execute to all users
        os.chmod(destination, stat.S_ENFMT)
        self.assertRaises(CopyConfigError,
                          self.test._copy_string,
                          src=source,
                          dst=destination)
        os.chmod(destination, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_search_config(self):
        full_path = self.test._search_config(self.config_name,
                                             None)
        result = PurePath(full_path)
        self.assertIsInstance(result, (str, PurePath))
        self.assertEqual(result.parts[-1], self.config_name)

    def test_wrong_search_config(self):
        self.assertRaises(NameConfigError,
                          self.test._set_configparser,
                          name=self.example_config,
                          directory=self.fixtures)

    def test_backup_file(self):
        result = self.test._backup_config_file()
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], str)
        self.assertIsInstance(result[1], PurePath)
        self.assertRegex(result[0], "Backup config.ini to:")
        # delete created backup file
        os.remove(result[1])

    def test_wrong_backup_file(self):
        self.test.root_directory = self.fixtures
        destination = self.test._search_config(name=self.config_name,
                                               directory=self.fixtures)
        # Change mode to not read, not write, not execute to all users
        os.chmod(destination, stat.S_ENFMT)
        self.assertRaises(BackupConfigError,
                          self.test._backup_config_file)
        # Change mode to read, write, execute to all users
        os.chmod(destination, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_validate(self):
        result = self.test._to_dict()
        self.assertIsInstance(result, dict)
        self.assertEqual(result['id'], "1234")
        self.assertEqual(result['type'], 'channel')
        self.assertEqual(result['name'], 'Канал')
        self.assertEqual(result['level'], '0')

    def test_rebuild_config(self):
        result = self.test._rebuild_config()
        self.assertEqual(result, 'Config rebuild success')

    def test_wrong_rebuild_config(self):
        destination = self.test._search_config(name=self.config_name,
                                               directory=self.fixtures)
        # Change mode to not read, not write, not execute to all users
        os.chmod(destination, stat.S_ENFMT)
        self.assertRaises(RebuildConfigError,
                          self.test._rebuild_config)
        # Change mode to read, write, execute to all users
        os.chmod(destination, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    def test_get_root_directory(self):
        directory = self.test.root_directory
        self.assertEqual(directory, None)

    def test_set_root_directory(self):
        self.test.root_directory = self.fixtures
        result = PurePath(self.test.file_path)
        self.assertEqual(result.parts[-1], self.config_name)
        self.assertEqual(result.parts[-2], 'fixtures')
        self.assertEqual(result.parts[-3], 'tests')

    def test_get_config_name(self):
        result = self.test.config_name
        self.assertEqual(result, self.config_name)

    def test_set_config_name(self):
        result = self.test.config_name = 'example_config.ini'
        self.assertEqual(result, 'example_config.ini')

    def test_read(self):
        result = self.test.read()
        self.assertEqual(result.id, "1234")
        self.assertEqual(result.type, 'channel')
        self.assertEqual(result.name, 'Канал')
        self.assertEqual(result.level, '0')

    def test_wrong_read(self):
        self.test.root_directory = self.fixtures

        def result(name):
            self.test.config_name = name
            return self.test.config_name

        self.assertRaises(MissingSectionHeaderError,
                          result,
                          'wrong_config.ini')

    def test_write_without_backup(self):
        self.test.root_directory = self.fixtures
        result = self.test.write(section='database',
                                 key="url",
                                 value="www.test.ru",
                                 backup=False)
        self.assertEqual(result[0], 'Completed')
        self.assertEqual(result[1], None)
        # rebuild config.ini to tests
        self.test._rebuild_config()

    def test_write_with_backup(self):
        self.test.root_directory = self.fixtures
        result = self.test.write(section='database',
                                 key="url",
                                 value="www.test.ru",
                                 backup=True)
        self.assertEqual(result[0], 'Completed')
        self.assertRegex(PurePath(result[1]).parts[-1],
                         'config.ini.BAK+')
        # rebuild config.ini to tests
        self.test._rebuild_config()
        # delete created backup file
        os.remove(result[1])

    def test_write_with_access_error(self):
        self.test.root_directory = self.fixtures
        self.test.config_name = self.config_name
        destination = self.test._search_config(name=self.config_name,
                                               directory=self.fixtures)
        # Change mode to not read, not write, not execute to all users
        os.chmod(destination, stat.S_ENFMT)
        self.assertRaises(AccessConfigError,
                          self.test.write,
                          section='database',
                          key="url",
                          value="www.test.ru",
                          backup=False)
        # Change mode to read, write, execute to all users
        os.chmod(destination, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        # rebuild config.ini to tests
        self.test._rebuild_config()
