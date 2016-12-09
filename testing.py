import unittest
import sys
sys.path.append('roomfinder_web/roomfinder_web')
import web_server

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        sys.stderr.write('Setup testing.')
        web_server.app.config['TESTING'] = True
        web_server.data_server=sys.argv[1]
        self.app = web_server.app.test_client()
 
    def test_correct_http_response(self):
        sys.stderr.write('Test HTTP GET / == 200.')
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)
    def test_about_correct_http_response(self):
        sys.stderr.write('Test HTTP GET /about == 200.')
        resp = self.app.get('/about')
        self.assertEquals(resp.status_code, 200)
    def test_form_correct_http_response(self):
        sys.stderr.write('Test HTTP GET /form == 200.')
        resp = self.app.get('/form')
        self.assertEquals(resp.status_code, 200)

    # def test_correct_content(self):
    #     resp = self.app.get('/hello/world')
    #     self.assertEquals(resp.data, '"Hello World!"\n')

    # def test_universe_correct_content(self):
    #     resp = self.app.get('/hello/universe')
    #     self.assertEquals(resp.data, '"Hello Universe!"\n')

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
