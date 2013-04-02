import types
import unittest
import sys

from environ import *


class BaseTests(unittest.TestCase):

    URL = 'http://www.google.com/'
    POSTGRES = 'postgres://uf07k1i6d8ia0v:wegauwhgeuioweg@ec2-107-21-253-135.compute-1.amazonaws.com:5431/d8r82722r2kuvn'
    MYSQL = 'mysql://bea6eb025ca0d8:69772142@us-cdbr-east.cleardb.com/heroku_97681db3eff7580?reconnect=true'
    SQLITE = 'sqlite:////full/path/to/your/database/file.sqlite'
    JSON = dict(one='bar', two=2, three=33.44)
    DICT = dict(foo='bar', test='on')
    PATH = '/home/dev'

    @classmethod
    def generateData(cls):
        return dict(STR_VAR='bar',
                    INT_VAR='42',
                    FLOAT_VAR='33.3',
                    BOOL_TRUE_VAR='1',
                    BOOL_TRUE_VAR2='True',
                    BOOL_FALSE_VAR='0',
                    BOOL_FALSE_VAR2='False',
                    PROXIED_VAR='$STR_VAR',
                    INT_LIST='42,33',
                    STR_LIST_WITH_SPACES=' foo,  bar',
                    EMPTY_LIST='',
                    DICT_VAR='foo=bar,test=on',
                    DATABASE_URL=cls.POSTGRES,
                    DATABASE_MYSQL_URL=cls.MYSQL,
                    DATABASE_SQLITE_URL=cls.SQLITE,
                    URL_VAR=cls.URL,
                    JSON_VAR=json.dumps(cls.JSON),
                    PATH_VAR=cls.PATH)

    def setUp(self):
        self.env = Env()
        self.environ = self.generateData()
        self._orig_environ = os.environ
        os.environ = self.environ

    def tearDown(self):
        os.environ = self._orig_environ

    def assertTypeAndValue(self, type_, expected, actual):
        self.assertEqual(type_, type(actual))
        self.assertEqual(expected, actual)


class EnvTests(BaseTests):

    def test_not_present_with_default(self):
        self.assertEqual(3, self.env('not_present', default=3))

    def test_not_present_without_default(self):
        with self.assertRaises(ImproperlyConfigured):
            self.env('not_present')

    def test_str(self):
        self.assertTypeAndValue(str, 'bar', self.env('STR_VAR'))
        self.assertTypeAndValue(str, 'bar', self.env.str('STR_VAR'))

    def test_int(self):
        self.assertTypeAndValue(int, 42, self.env('INT_VAR', cast=int))
        self.assertTypeAndValue(int, 42, self.env.int('INT_VAR'))

    def test_int_with_none_default(self):
        self.assertTypeAndValue(types.NoneType, None,
                                self.env('NOT_PRESENT_VAR', cast=int, default=None))

    def test_float(self):
        self.assertTypeAndValue(float, 33.3, self.env('FLOAT_VAR', cast=float))
        self.assertTypeAndValue(float, 33.3, self.env.float('FLOAT_VAR'))

    def test_bool_true(self):
        self.assertTypeAndValue(bool, True, self.env('BOOL_TRUE_VAR', cast=bool))
        self.assertTypeAndValue(bool, True, self.env('BOOL_TRUE_VAR2', cast=bool))
        self.assertTypeAndValue(bool, True, self.env.bool('BOOL_TRUE_VAR'))

    def test_bool_false(self):
        self.assertTypeAndValue(bool, False, self.env('BOOL_FALSE_VAR', cast=bool))
        self.assertTypeAndValue(bool, False, self.env('BOOL_FALSE_VAR2', cast=bool))
        self.assertTypeAndValue(bool, False, self.env.bool('BOOL_FALSE_VAR'))

    def test_proxied_value(self):
        self.assertTypeAndValue(str, 'bar', self.env('PROXIED_VAR'))

    def test_int_list(self):
        self.assertTypeAndValue(list, [42, 33], self.env('INT_LIST', cast=[int]))
        self.assertTypeAndValue(list, [42, 33], self.env.list('INT_LIST', int))

    def test_str_list_with_spaces(self):
        self.assertTypeAndValue(list, [' foo', '  bar'],
                                self.env('STR_LIST_WITH_SPACES', cast=[str]))
        self.assertTypeAndValue(list, [' foo', '  bar'],
                                self.env.list('STR_LIST_WITH_SPACES'))

    def test_empty_list(self):
        self.assertTypeAndValue(list, [], self.env('EMPTY_LIST', cast=[int]))

    def test_dict_value(self):
        self.assertTypeAndValue(dict, self.DICT, self.env.dict('DICT_VAR'))

    def test_dict_parsing(self):

        self.assertEqual({'a': '1'}, self.env.parse_value('a=1', dict))
        self.assertEqual({'a': 1}, self.env.parse_value('a=1', dict(value=int)))
        self.assertEqual({'a': ['1', '2', '3']}, self.env.parse_value('a=1,2,3', dict(value=[str])))
        self.assertEqual({'a': [1, 2, 3]}, self.env.parse_value('a=1,2,3', dict(value=[int])))
        self.assertEqual({'a': 1, 'b': [1.1, 2.2], 'c': 3},
                         self.env.parse_value('a=1;b=1.1,2.2;c=3', dict(value=int, cast=dict(b=[float]))))

    def test_url_value(self):
        url = self.env.url('URL_VAR')
        self.assertEqual(url.__class__, self.env.URL_CLASS)
        self.assertEqual(url.geturl(), self.URL)

    def test_db_url_value(self):
        pg_config = self.env.db()
        self.assertEqual(pg_config['ENGINE'], 'django.db.backends.postgresql_psycopg2')
        self.assertEqual(pg_config['NAME'], 'd8r82722r2kuvn')
        self.assertEqual(pg_config['HOST'], 'ec2-107-21-253-135.compute-1.amazonaws.com')
        self.assertEqual(pg_config['USER'], 'uf07k1i6d8ia0v')
        self.assertEqual(pg_config['PASSWORD'], 'wegauwhgeuioweg')
        self.assertEqual(pg_config['PORT'], 5431)

        mysql_config = self.env.db('DATABASE_MYSQL_URL')
        self.assertEqual(mysql_config['ENGINE'], 'django.db.backends.mysql')
        self.assertEqual(mysql_config['NAME'], 'heroku_97681db3eff7580')
        self.assertEqual(mysql_config['HOST'], 'us-cdbr-east.cleardb.com')
        self.assertEqual(mysql_config['USER'], 'bea6eb025ca0d8')
        self.assertEqual(mysql_config['PASSWORD'], '69772142')
        self.assertEqual(mysql_config['PORT'], None)

        sqlite_config = self.env.db('DATABASE_SQLITE_URL')
        self.assertEqual(sqlite_config['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(sqlite_config['NAME'], '/full/path/to/your/database/file.sqlite')

    def test_json_value(self):
        self.assertEqual(self.JSON, self.env.json('JSON_VAR'))

    def test_path(self):
        root = self.env.path('PATH_VAR')
        self.assertTypeAndValue(Path, Path(self.PATH), root)


class FileEnvTests(EnvTests):

    def setUp(self):
        self.env = Env()
        self._orig_environ = os.environ
        os.environ = {}
        file_path = Path(__file__, is_file=True)('test_env.txt')
        self.env.read_env(file_path, PATH_VAR=Path(__file__, is_file=True).__root__)


class SchemaEnvTests(BaseTests):

    def test_schema(self):
        env = Env(INT_VAR=int, NOT_PRESENT_VAR=(float, 33.3), STR_VAR=str,
                  INT_LIST=[int], DEFAULT_LIST=([int], [2]))

        self.assertTypeAndValue(int, 42, env('INT_VAR'))
        self.assertTypeAndValue(float, 33.3, env('NOT_PRESENT_VAR'))

        self.assertTypeAndValue(str, 'bar', env('STR_VAR'))
        self.assertTypeAndValue(str, 'foo', env('NOT_PRESENT2', default='foo'))

        self.assertTypeAndValue(list, [42, 33], env('INT_LIST'))
        self.assertTypeAndValue(list, [2], env('DEFAULT_LIST'))

        # Override schema in this one case
        self.assertTypeAndValue(str, '42', env('INT_VAR', cast=str))


class PathTests(unittest.TestCase):

    def test_path_class(self):

        root = Path(__file__, '..', is_file=True)
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))
        self.assertEqual(root(), root_path)
        self.assertEqual(root.__root__, root_path)

        web = root.path('public')
        self.assertEqual(web(), os.path.join(root_path, 'public'))
        self.assertEqual(web('css'), os.path.join(root_path, 'public', 'css'))

    def test_required_path(self):

        with self.assertRaises(ImproperlyConfigured):
            Path('/not/existing/path/', required=True)

        with self.assertRaises(ImproperlyConfigured):
            root = Path(__file__)
            root('not_existing_path', required=True)

    def test_comparison(self):

        self.assertTrue(Path('/home') in Path('/'))
        self.assertTrue(Path('/home') not in Path('/other/dir'))

        self.assertTrue(Path('/home') == Path('/home'))
        self.assertTrue(Path('/home') != Path('/home/dev'))

        self.assertEqual(~Path('/home'), Path('/'))
        self.assertEqual(Path('/') + 'home', Path('/home'))
        self.assertEqual(Path('/') + 'home' + Path('/public'), Path('/home/public'))
        self.assertEqual(Path('/home/dev/public') - 2, Path('/home'))

        with self.assertRaises(TypeError):
            Path('/home/dev/') - 'not int'


def load_suite():

    test_suite = unittest.TestSuite()
    for case in [EnvTests, FileEnvTests, SchemaEnvTests, PathTests]:
        test_suite.addTest(unittest.makeSuite(case))
    return test_suite

if __name__ == "__main__":

    try:
        if sys.argv[1] == '-o':
            for key, value in BaseTests.generateData().items():
                print "{0}={1}".format(key, value)
            sys.exit()
    except IndexError:
        pass

    unittest.TextTestRunner().run(load_suite())
