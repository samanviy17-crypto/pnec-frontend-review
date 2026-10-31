"""Manual static build. Writes only a NEW destination; never publishes or changes DNS."""
import argparse
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
from urllib.parse import urlsplit


def origin(value):
    parsed=urlsplit(value)
    if (parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password
            or parsed.path not in ('','/') or parsed.query or parsed.fragment or parsed.port not in (None,443)):
        raise ValueError('Provide an HTTPS root origin without credentials, path or query')
    return value.rstrip('/')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination',type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    destination=args.destination.absolute()
    if destination.exists() or destination==root or root in destination.parents:
        raise ValueError('Destination must be new and outside source')
    frontend=origin(os.environ['PNEC_FRONTEND_ORIGIN'])
    backend=origin(os.environ['PNEC_API_ORIGIN'])
    contact=os.environ['PNEC_CONTACT_EMAIL']
    if not re.fullmatch(r'[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}',contact):
        raise ValueError('Supply the organization-approved public contact email')
    donation=os.environ.get('PNEC_DONATION_URL','')
    if donation:
        parsed=urlsplit(donation)
        if parsed.scheme!='https' or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('Donation destination must be owner-approved HTTPS')
    with tempfile.TemporaryDirectory(prefix='pnec-build-') as temporary:
        config=Path(temporary)/'production.yml'
        config.write_text(json.dumps({'url':frontend,'baseurl':'','api_base_url':backend,'title':'Poway Neighborhood Emergency Corps','donation_url':donation,'contact_email':contact,'sass':{'cache':False,'cache_location':str(Path(temporary)/'sass-cache')}}))
        subprocess.run(['bundle','exec','jekyll','build','--source',str(root),'--destination',str(destination),'--config',str(root/'_config.yml')+','+str(config)],cwd=temporary,env={**os.environ,'BUNDLE_GEMFILE':str(root/'Gemfile'),'JEKYLL_ENV':'production'},check=True)
    # Replace sanitized public-contact placeholders in static JSON and chatbot
    # instructions too. Exact mailbox boundaries prevent repeated replacement of
    # an already configured address such as public-contact@example.test.
    placeholder=re.compile(r'(?<![A-Za-z0-9._%+-])contact@example\.test(?![A-Za-z0-9.-])')
    for output in destination.rglob('*'):
        if output.is_file() and output.suffix in ('.html','.js','.json'):
            text=output.read_text()
            updated=placeholder.sub(lambda _:contact,text)
            if updated!=text:output.write_text(updated)
    print('Built static artifact; no hosting or domain settings changed.')

if __name__=='__main__':main()
