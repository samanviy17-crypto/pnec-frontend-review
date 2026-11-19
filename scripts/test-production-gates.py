"""Offline negative release-gate checks; no server contact, publication or secrets."""
import importlib.util,io,json,ssl,unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('production_build',Path(__file__).with_name('build-production.py'))
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class Response(io.StringIO):
    def __init__(self,data,**headers):
        super().__init__(json.dumps(data));self.headers=Message()
        self.headers['Access-Control-Allow-Origin']=module.FRONTEND
        self.headers['Access-Control-Allow-Credentials']='true'
        for k,v in headers.items():self.headers[k.replace('_','-')]=v

def responses():
    return [Response({'status':'ok','review':False}),Response({'status':'ready','schema_revision':module.SCHEMA}),Response({},Access_Control_Allow_Methods='GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS',Access_Control_Allow_Headers='Authorization,Content-Type,X-CSRF-Token')]

class Gates(unittest.TestCase):
    def test_valid_read_only_gate(self):
        with patch.object(module,'urlopen',side_effect=responses()) as opened:module.verify_live_api()
        self.assertEqual([x.args[0].get_method() for x in opened.call_args_list],['GET','GET','OPTIONS'])
        self.assertTrue(all(x.args[0].full_url.startswith(module.API+'/api/') for x in opened.call_args_list))

    def test_duplicate_or_unapproved_cors(self):
        for duplicate in [False,True]:
            rs=responses()
            if duplicate:rs[0].headers['Access-Control-Allow-Origin']='https://untrusted.example'
            else:rs[0].headers.replace_header('Access-Control-Allow-Origin','https://untrusted.example')
            with self.subTest(duplicate=duplicate),patch.object(module,'urlopen',side_effect=rs),self.assertRaises(SystemExit):module.verify_live_api()

    def test_review_or_stale_schema(self):
        for idx,data in [(0,{'status':'ok','review':True}),(1,{'status':'ready','schema_revision':'0001_pnec_release'})]:
            rs=responses();rs[idx]=Response(data)
            with self.subTest(data=data),patch.object(module,'urlopen',side_effect=rs),self.assertRaises(SystemExit):module.verify_live_api()

    def test_missing_patch_or_csrf_header(self):
        for key in ['Access-Control-Allow-Methods','Access-Control-Allow-Headers']:
            rs=responses();rs[2].headers.replace_header(key,'GET' if key.endswith('Methods') else 'Content-Type')
            with self.subTest(header=key),patch.object(module,'urlopen',side_effect=rs),self.assertRaises(SystemExit):module.verify_live_api()

    def test_tls_failure_has_no_insecure_retry(self):
        with patch.object(module,'urlopen',side_effect=ssl.SSLCertVerificationError('Synthetic hostname mismatch')) as opened,self.assertRaises(ssl.SSLCertVerificationError):module.verify_live_api()
        self.assertEqual(opened.call_count,1)

if __name__=='__main__':unittest.main()
