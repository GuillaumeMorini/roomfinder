import unittest
import sys
import os
sys.path.append('roomfinder_spark/roomfinder_spark')
import spark_bot

class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        sys.stderr.write('Setup testing.\n')
        #web_server.data_server = os.getenv("roomfinder_data_server")
        #web_server.book_url = os.getenv("roomfinder_book_server")
        spark_bot.app.config['TESTING'] = True
        self.app = spark_bot.app.test_client()
 
    def test_correct_http_response(self):
        sys.stderr.write('Test HTTP GET /demoroom/members == 200.\n')
        resp = self.app.get('/demoroom/members')
        self.assertEquals(resp.status_code, 200)

    #def test_about_correct_http_response(self):
    #    sys.stderr.write('Test HTTP GET /about == 200.\n')
    #    resp = self.app.get('/about')
    #    self.assertEquals(resp.status_code, 200)
    #def test_form_correct_http_response(self):
    #    sys.stderr.write('Test HTTP GET /form == 200.\n')
    #    resp = self.app.get('/form')
    #    self.assertEquals(resp.status_code, 200)

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
