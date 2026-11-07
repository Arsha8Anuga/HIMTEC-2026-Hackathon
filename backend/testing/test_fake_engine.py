import json
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from fake_engine import Handler

class FakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}/engine/v1'
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()
    def call(self, path, payload=None):
        req = Request(self.base + path, data=None if payload is None else json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
        try: response = urlopen(req, timeout=2)
        except HTTPError as err: response = err
        with response:
            self.assertEqual(response.headers['X-Fake-Engine'], 'true')
            return response.status, json.load(response)
    def test_health(self):
        status, body = self.call('/health'); self.assertEqual(status,200); self.assertFalse(body['data']['who_tables_loaded'])
    def test_growth_and_empty_history(self):
        for measurements in [[], [{'id':'fixture','measured_at':'2026-02-01','weight_kg':8}]]:
            status, body = self.call('/growth/evaluate', {'as_of':'2026-02-01','child':{'birth_date':'2026-01-01'},'measurements':measurements,'kpsp_results':[],'food_recalls':[]})
            self.assertEqual(status,200); self.assertEqual(len(body['data']['per_measurement']),len(measurements))
            if measurements: self.assertIsNone(body['data']['per_measurement'][0]['z']['wfa'])
    def test_reference_has_no_fabricated_who_data(self):
        status,body=self.call('/reference?indicator=lhfa');self.assertEqual(status,200);self.assertTrue(all(v==[] for v in body['data'].values()))
    def test_questionnaire_and_score(self):
        status,body=self.call('/kpsp/questionnaire?age_months=9');self.assertEqual(status,200);self.assertEqual(len(body['data']['items']),10)
        status,body=self.call('/kpsp/score',{'answers':[{'item_no':i,'answer':True} for i in range(1,11)]});self.assertEqual(status,200);self.assertEqual(body['data']['yes_count'],10)
    def test_invalid_and_unknown(self):
        self.assertEqual(self.call('/growth/evaluate',{})[0],422)
        self.assertEqual(self.call('/kpsp/score',{'answers':[]})[0],422)
        self.assertEqual(self.call('/unknown')[0],404)
if __name__ == '__main__': unittest.main()
