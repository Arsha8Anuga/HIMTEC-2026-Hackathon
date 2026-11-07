"""LOCAL TEST FIXTURE ONLY. No WHO/KPSP medical evaluation is performed."""
import argparse
import json
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

BASE = '/engine/v1'

class Handler(BaseHTTPRequestHandler):
    def reply(self, status, data=None, code=None, message=None):
        body = json.dumps({'data': data, 'error': None if code is None else {'code': code, 'message': message}}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('X-Fake-Engine', 'true')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == BASE + '/health':
            self.reply(200, {'status': 'ok', 'who_tables_loaded': False})
        elif path == BASE + '/reference':
            self.reply(200, {key: [] for key in ['x', 'sd_neg3', 'sd_neg2', 'median', 'sd_pos2', 'sd_pos3']})
        elif path == BASE + '/kpsp/questionnaire':
            self.reply(200, {'questionnaire_age_months': 9, 'review_status': 'transcription_unreviewed', 'items': [{'item_no': i, 'aspect': 'gerak_kasar', 'question': f'[DUMMY TEST] Pilih jawaban uji nomor {i}; bukan pertanyaan KPSP.'} for i in range(1, 11)]})
        else:
            self.reply(404, code='NOT_FOUND', message='Route fake engine tidak ditemukan')

    def do_POST(self):
        if urlsplit(self.path).path not in [BASE + '/growth/evaluate', BASE + '/kpsp/score']:
            self.reply(404, code='NOT_FOUND', message='Route fake engine tidak ditemukan')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024 * 1024:
                raise ValueError('Body harus berisi JSON, maksimal 1 MiB')
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError('Body harus objek JSON')
            if urlsplit(self.path).path == BASE + '/kpsp/score':
                answers = payload['answers']
                if (not isinstance(answers, list) or len(answers) != 10
                    or {a['item_no'] for a in answers} != set(range(1, 11))
                    or any(type(a['answer']) is not bool for a in answers)):
                    raise ValueError('Diperlukan 10 jawaban boolean unik')
                # Static outcome to exercise persistence only, NOT KPSP scoring.
                self.reply(200, {'yes_count': sum(a['answer'] for a in answers), 'result': 'sesuai'})
                return
            birth = date.fromisoformat(payload['child']['birth_date'])
            date.fromisoformat(payload['as_of'])
            for key in ['measurements', 'kpsp_results', 'food_recalls']:
                if not isinstance(payload[key], list):
                    raise ValueError(key + ' harus array')
            points = [{'id': m['id'], 'age_days': (date.fromisoformat(m['measured_at']) - birth).days,
                       'corrected_length_cm': m.get('length_height_cm'),
                       'z': {key: None for key in ['wfa', 'lhfa', 'wfl_wfh', 'hcfa']},
                       'classification': {}, 'flags': []} for m in payload['measurements']]
            # Fixed protocol fixtures. No level, age schedule or diet is assessed.
            self.reply(200, {'per_measurement': points, 'level': 'green', 'reasons': [],
                             'next_kpsp': {'questionnaire_age_months': 9, 'due': True}, 'diet': None})
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            self.reply(422, code='VALIDATION_ERROR', message='Fake engine: input tidak valid (' + str(exc) + ')')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fake engine lokal, bukan penilaian kesehatan.')
    parser.add_argument('--testing-only', action='store_true', required=True)
    parser.add_argument('--port', type=int, default=18001)
    args = parser.parse_args()
    print('FAKE ENGINE: fixture protokol saja. Label Aman/sesuai BUKAN hasil kesehatan.', flush=True)
    print(f'ENGINE_URL=http://127.0.0.1:{args.port}/engine/v1', flush=True)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
