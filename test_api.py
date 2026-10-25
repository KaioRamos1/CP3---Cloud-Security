import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from wsgiref.validate import validator
from wsgiref.util import setup_testing_defaults
import app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_db = app.DB_PATH
        app.DB_PATH = Path(self.temp.name) / 'test.sqlite3'
        app.init_database(seed=True)

    def tearDown(self):
        app.DB_PATH = self.original_db
        self.temp.cleanup()

    def call(self, method, path, data=None, headers=None, raw=None):
        env = {}
        setup_testing_defaults(env)
        body = raw if raw is not None else json.dumps(data).encode() if data is not None else b''
        url, _, query = path.partition('?')
        env.update(REQUEST_METHOD=method, PATH_INFO=url, QUERY_STRING=query,
                   CONTENT_TYPE='application/json', CONTENT_LENGTH=str(len(body)),
                   HTTP_X_REQUESTED_WITH='MinhaFrota')
        env['wsgi.input'] = io.BytesIO(body)
        env.update(headers or {})
        status = {}
        def start(line, output_headers, exc_info=None):
            status['code'] = int(line.split()[0]);status['headers'] = dict(output_headers)
        # A malformed Content-Length is intentionally outside valid WSGI input.
        handler = app.application if env.get('CONTENT_LENGTH') == '-1' else validator(app.application)
        result = handler(env, start)
        response = b''.join(result)
        if hasattr(result, 'close'): result.close()
        return status['code'], json.loads(response) if response and status['headers'].get('Content-Type','').startswith('application/json') else response, status['headers']

    def vehicle(self, **values):
        return dict(type='carro', brand='Teste', model='Cloud', year=2026, plate='TST1A23', **values)

    def test_health_does_not_expose_filesystem(self):
        code, data, _ = self.call('GET', '/api/health')
        self.assertEqual((code, data), (200, {'status':'ok','database':'ok'}))

    def test_seed_runs_only_once(self):
        app.init_database(seed=True)
        self.assertEqual(len(self.call('GET','/api/vehicles')[1]['data']),3)
        for ident in (1,2,3): self.call('DELETE',f'/api/vehicles/{ident}?confirm=true')
        app.init_database(seed=True)
        self.assertEqual(self.call('GET','/api/vehicles')[1]['data'],[])

    def test_vehicle_crud_and_empty_204(self):
        code, data, _ = self.call('POST','/api/vehicles',self.vehicle())
        self.assertEqual(code,201);ident=data['data']['id']
        self.assertEqual(self.call('PUT',f'/api/vehicles/{ident}',{'brand':'Atualizada'})[0],200)
        self.assertEqual(self.call('GET',f'/api/vehicles/{ident}')[1]['data']['brand'],'Atualizada')
        self.assertEqual(self.call('DELETE',f'/api/vehicles/{ident}')[0],409)
        code, body, headers = self.call('DELETE',f'/api/vehicles/{ident}?confirm=true')
        self.assertEqual((code,body),(204,b''))
        self.assertNotIn('Content-Length',headers)
        self.assertEqual(self.call('GET',f'/api/vehicles/{ident}')[0],404)

    def test_record_crud_and_cascade(self):
        payload={'vehicle_id':2,'kind':'despesa','category':'Teste','description':'Lavagem','amount':50}
        code,data,_=self.call('POST','/api/records',payload);self.assertEqual(code,201)
        ident=data['data']['id']
        self.assertEqual(self.call('PUT',f'/api/records/{ident}',{'status':'pago','performed_on':'2026-10-25'})[0],200)
        self.assertEqual(self.call('GET',f'/api/records/{ident}')[0],200)
        self.call('DELETE','/api/vehicles/2?confirm=true')
        self.assertEqual(self.call('GET',f'/api/records/{ident}')[0],404)

    def test_duplicate_plate(self):
        self.call('POST','/api/vehicles',self.vehicle())
        self.assertEqual(self.call('POST','/api/vehicles',self.vehicle())[0],409)

    def test_invalid_foreign_key(self):
        self.assertEqual(self.call('POST','/api/records',{'vehicle_id':999,'kind':'despesa','category':'X','description':'X'})[0],409)

    def test_validation_types_and_required_fields(self):
        for field,value in [('year',True),('brand',None),('brand',' '),('model',[]),('plate','erro'),('odometer_km',-1),('odometer_km',True),('odometer_km',1e20),('status','outro')]:
            with self.subTest(field=field,value=value):
                data=self.vehicle();data[field]=value
                self.assertEqual(self.call('POST','/api/vehicles',data)[0],400)
        for data in ([],None,{}, {'is_demo':1}): self.assertEqual(self.call('POST','/api/vehicles',data)[0],400)

    def test_dates_and_amount(self):
        base={'vehicle_id':1,'kind':'despesa','category':'X','description':'X'}
        for extra in ({'due_date':'2026-02-30'}, {'amount':-1}, {'amount':True}, {'status':'x'}):
            self.assertEqual(self.call('POST','/api/records',dict(base,**extra))[0],400)

    def test_sql_values_are_not_executed(self):
        payload=self.vehicle();payload['brand']="'); DROP TABLE vehicles; --"
        self.assertEqual(self.call('POST','/api/vehicles',payload)[0],201)
        self.assertEqual(len(self.call('GET','/api/vehicles')[1]['data']),4)

    def test_unknown_column_is_rejected(self):
        self.assertEqual(self.call('PUT','/api/vehicles/1',{'brand = NULL --':'x'})[0],400)

    def test_json_and_media_type(self):
        self.assertEqual(self.call('POST','/api/vehicles',raw=b'{')[0],400)
        self.assertEqual(self.call('POST','/api/vehicles',raw=b'{"year": NaN}')[0],400)
        self.assertEqual(self.call('POST','/api/vehicles',self.vehicle(),{'CONTENT_TYPE':'text/plain'})[0],415)

    def test_request_size_limit(self):
        self.assertEqual(self.call('POST','/api/vehicles',raw=b'x'*(app.MAX_BODY+1))[0],413)
        self.assertEqual(self.call('POST','/api/vehicles',headers={'CONTENT_LENGTH':'-1'})[0],400)

    def test_csrf_and_no_cors(self):
        self.assertEqual(self.call('POST','/api/vehicles',self.vehicle(),{'HTTP_X_REQUESTED_WITH':''})[0],403)
        self.assertEqual(self.call('DELETE','/api/vehicles/1?confirm=true',headers={'HTTP_X_REQUESTED_WITH':''})[0],403)
        self.assertEqual(self.call('OPTIONS','/api/vehicles')[0],405)
        self.assertNotIn('Access-Control-Allow-Origin',self.call('GET','/api/vehicles')[2])

    def test_security_headers_and_static_allowlist(self):
        _,_,headers=self.call('GET','/')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertIn("script-src 'self'",headers['Content-Security-Policy'])
        self.assertEqual(self.call('GET','/static/../../app.py')[0],404)
        self.assertEqual(self.call('GET','/static/app.js')[0],200)

    def test_monthly_cost_excludes_other_months(self):
        self.call('POST','/api/records',{'vehicle_id':1,'kind':'despesa','category':'X','description':'Antigo','amount':900,'due_date':'2000-01-01'})
        self.assertEqual(self.call('GET','/api/dashboard')[1]['data']['monthly_cost'],480)

    def test_filters(self):
        self.assertEqual(len(self.call('GET','/api/vehicles?type=moto')[1]['data']),1)
        self.assertEqual(self.call('GET','/api/vehicles?type=outro')[0],400)
        self.assertEqual(self.call('GET','/api/records?vehicle_id=x')[0],400)

    def test_database_persistence_and_backup(self):
        self.call('POST','/api/vehicles',self.vehicle())
        app.init_database(seed=False)
        with app.closing(app.connect()) as source, app.closing(sqlite3.connect(Path(self.temp.name)/'backup.sqlite3')) as backup:
            source.backup(backup)
            self.assertEqual(backup.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            self.assertEqual(backup.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0],4)

    def test_xss_payload_is_data_and_dom_uses_text(self):
        payload=self.vehicle();payload['brand']='<img src=x onerror=alert(1)>'
        self.assertEqual(self.call('POST','/api/vehicles',payload)[0],201)
        script=(app.ROOT/'static/app.js').read_text()
        self.assertNotIn('innerHTML',script)
        self.assertIn('textContent',script)


if __name__ == '__main__': unittest.main(verbosity=2)
