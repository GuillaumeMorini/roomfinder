import unittest
import sys
sys.path.append('roomfinder_web/roomfinder_web')
import web_server

class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        web_server.app.config['TESTING'] = True
        self.app = demoapp.app.test_client()
 
    def test_correct_http_response(self):
        resp = self.app.get('/')
        self.assertEquals(resp.status_code, 200)
    def test_about_correct_http_response(self):
        resp = self.app.get('/about')
        self.assertEquals(resp.status_code, 200)
    def test_form_correct_http_response(self):
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
