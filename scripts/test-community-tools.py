"""Release regression: test-community-tools.py.

Run through scripts/run-release-tests.py with explicit frontend/backend roots.
Uses only the disposable build and isolated backend state selected by the runner.
"""
import functools
import os
import json
from pathlib import Path
import sys
import threading
import tempfile
import secrets
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timedelta, timezone

from release_test_support import FRONTEND_ROOT, BACKEND_ROOT, SITE_ROOT, PREVIEW_URL
from app.config import Config
test_state = tempfile.TemporaryDirectory(prefix='pnec-release-community-')
Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(Path(test_state.name) / 'community.db')
Config.SECRET_KEY = secrets.token_hex(32)
Config.UPLOAD_FOLDER = str(Path(test_state.name) / 'uploads')
Config.ADMIN_PASSWORD = 'browser-test-only-password-2026'
from app import create_app, db
from app.models.user import User
from app.models.neighborhood import Neighborhood
from app.services import risk_service
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server

app = create_app()
app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
risk_service.get_risk_assessment = lambda *args, **kwargs: {
    'fire_level':'LOW', 'flood_level':'HIGH', 'heat_level':'LOW',
    'fire_score':1, 'flood_score':8, 'heat_score':1,
    'updated_at':'2026-10-05T12:00:00', 'is_stale':False,
}
accounts = {}
with app.app_context():
    nid = Neighborhood.query.first().id
    for name, role in [('resident','resident'), ('staff','staff'), ('coordinator','coordinator')]:
        user = User(email=name+'@example.test', display_name=name, role=role,
                    password_hash='unused', neighborhood_id=nid)
        user.generate_token(); db.session.add(user); db.session.flush()
        if role == 'coordinator':
            app.config['COORDINATOR_ASSIGNMENTS'] = {str(user.id): nid}
        accounts[name] = {'token':user.auth_token, 'user':user.to_dict()}
    db.session.commit()

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

site = SITE_ROOT
assert (site / 'pages/checklist.html').exists(), 'Build the frontend first.'
# The runner owns the disposable preview; this script owns only its backend.
backend = make_server('127.0.0.1',0,app,threaded=True)
for server in (backend,):
    threading.Thread(target=server.serve_forever,daemon=True).start()

try:
    with sync_playwright() as play:
        browser = play.chromium.launch()
        def account(name):
            context = browser.new_context()
            data = accounts[name]
            context.add_init_script('window.PNEC_CHATBOT_CONFIG = {apiBase: '+json.dumps('http://127.0.0.1:'+str(backend.server_port))+'};')
            context.add_init_script('localStorage.setItem("pnec_token", '+json.dumps(data['token'])+'); localStorage.setItem("pnec_user", '+json.dumps(json.dumps(data['user']))+');')
            # Keep browser verification local; inherited CDN widgets may be unavailable.
            context.route('**/*', lambda route: route.continue_() if route.request.url.startswith((PREVIEW_URL + '/', 'http://127.0.0.1:' + str(backend.server_port) + '/')) else route.abort())
            if backend.server_port != 8425:
                context.route('http://127.0.0.1:8425/**', lambda route: route.continue_(url=route.request.url.replace(':8425', ':'+str(backend.server_port), 1)))
            page = context.new_page()
            return context, page
        resident_context, resident = account('resident')
        staff_context, staff = account('staff')
        coordinator_context, coordinator = account('coordinator')
        def visit(page,path):
            page.goto(PREVIEW_URL+path,wait_until='domcontentloaded')
        def area(page,title):
            return page.locator('.community-tools section').filter(has=page.get_by_role('heading',name=title,exact=True)).last

        visit(resident,'/pages/checklist.html')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')
        resident.locator('#cb-water').check()
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')
        plan = area(resident,'Your household plan')
        plan.get_by_label('People in your household').fill('4')
        plan.get_by_label('Meeting point',exact=True).fill('Community library')
        plan.get_by_label('Household evacuation plan and access needs').fill('Review our neighborhood map together')
        plan.get_by_role('button',name='Save household plan',exact=True).click()
        expect(plan.get_by_role('status')).to_have_text('Saved.')
        expect(resident.locator('#cb-water').locator('..').locator('.checklist-item-qty')).to_have_text('12 gallons / household')
        quiz = area(resident,'Preparedness assessment')
        for choice in quiz.locator('select').all(): choice.select_option('yes')
        quiz.get_by_role('button',name='Save assessment',exact=True).click()
        expect(quiz.get_by_role('status').first).to_contain_text('100%')
        checkin = area(resident,'Resident well-being check-in')
        checkin.get_by_label('My status').select_option('need_help')
        checkin.get_by_label('Details for your coordinator').fill('Please check on our household')
        checkin.get_by_role('button',name='Update my status',exact=True).click()
        expect(checkin.get_by_role('heading',name='resident: Need help')).to_be_visible()
        hazard = area(resident,'Report a neighborhood hazard')
        hazard.get_by_label('Neighborhood',exact=True).select_option(str(nid))
        hazard.get_by_label('Hazard type').select_option('route')
        hazard.get_by_label('Location',exact=True).fill('Test street')
        hazard.get_by_label('Description',exact=True).fill('Test blocked route')
        hazard.get_by_role('button',name='Submit hazard report',exact=True).click()
        expect(hazard.get_by_role('heading',name='Test street · open')).to_be_visible()
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#cb-water')).to_be_checked()
        expect(area(resident,'Your household plan').get_by_label('Meeting point',exact=True)).to_have_value('Community library')
        expect(area(resident,'Preparedness assessment').get_by_role('status').first).to_contain_text('100%')

        # Failed saves survive reload; untouched server items are merged.
        def unavailable(route): route.abort()
        resident.route('**/api/preparedness', unavailable)
        resident.locator('#cb-water').uncheck()
        expect(resident.locator('#kit-sync-status')).to_contain_text('Account save failed')
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#kit-sync-status')).to_contain_text('Account checklist unavailable')
        expect(resident.locator('#cb-water')).not_to_be_checked()
        expect(resident.locator('#cb-food')).to_be_enabled()
        resident.locator('#cb-food').check()
        from app.models.operations import HouseholdPreparedness
        with app.app_context():
            household = db.session.get(HouseholdPreparedness, accounts['resident']['user']['id'])
            household.items = {**household.items, 'radio': True}
            db.session.commit()
        resident.unroute('**/api/preparedness', unavailable)
        resident.evaluate('pnecRetryKit()')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')
        expect(resident.locator('#cb-water')).not_to_be_checked()
        expect(resident.locator('#cb-food')).to_be_checked()
        expect(resident.locator('#cb-radio')).to_be_checked()
        # Account verification failure must not disable local editing either.
        resident.route('**/api/auth/me', unavailable)
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#kit-sync-status')).to_contain_text('Account unavailable')
        expect(resident.locator('#cb-water')).to_be_enabled()
        resident.locator('#cb-water').check()
        resident.unroute('**/api/auth/me', unavailable)
        resident.evaluate('pnecRetryKit()')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')

        # An older acknowledgement must not clear a newer edit, even if values repeat.
        resident.evaluate("""() => {
            window.originalChecklistRequest = window.pnecCommunityRequest;
            let saves = 0;
            window.pnecCommunityRequest = (...args) => args[1] === 'PATCH' && ++saves > 1
                ? Promise.reject(new Error('queued save unavailable'))
                : window.originalChecklistRequest(...args);
            const box = document.getElementById('cb-water');
            for (const value of [false, true, false]) {
                box.checked = value; box.dispatchEvent(new Event('change'));
            }
        }""")
        expect(resident.locator('#kit-sync-status')).to_contain_text('queued save unavailable')
        resident.wait_for_function("JSON.parse(localStorage.getItem('pnec_kit_' + JSON.parse(localStorage.getItem('pnec_user')).id + '_pending')).water === false")
        resident.evaluate('window.pnecCommunityRequest = window.originalChecklistRequest; pnecRetryKit()')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')

        # Pre-outbox browser copies are kept until the resident explicitly reconciles.
        resident.evaluate("""() => {
            const key = 'pnec_kit_' + JSON.parse(localStorage.getItem('pnec_user')).id;
            localStorage.setItem(key, JSON.stringify({water:true}));
            localStorage.removeItem(key + '_pending');
            localStorage.removeItem(key + '_review');
        }""")
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#kit-sync-status')).to_contain_text('Browser choices are retained')
        expect(resident.locator('#cb-water')).to_be_checked()
        resident.reload(wait_until='domcontentloaded')
        expect(resident.locator('#kit-sync-status')).to_contain_text('Browser choices are retained')
        with app.app_context():
            assert db.session.get(HouseholdPreparedness, accounts['resident']['user']['id']).items['water'] is False, 'Legacy browser choices saved without explicit retry'
        resident.evaluate('pnecRetryKit()')
        expect(resident.locator('#kit-sync-status')).to_have_text('Saved to your account.')

        visit(coordinator,'/pages/dashboard.html')
        expect(coordinator.get_by_role('heading',name='resident: Need help')).to_be_visible()
        coordinator.get_by_role('button',name='Mark resolved',exact=True).click()
        expect(coordinator.get_by_role('heading',name='Test street · resolved')).to_be_visible()
        visit(coordinator,'/pages/volunteer.html')
        tasks = area(coordinator,'Volunteer shifts and tasks')
        tasks.get_by_label('Task or shift title').fill('Test training shift')
        tasks.get_by_label('Details and meeting location').fill('Community center')
        tasks.get_by_label('Neighborhood',exact=True).select_option(str(nid))
        tasks.get_by_label('Start date and time (your local time)').fill((datetime.now()+timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'))
        tasks.get_by_label('Available slots').fill('1')
        tasks.get_by_role('button',name='Post a shift',exact=True).click()
        expect(tasks.get_by_role('heading',name='Test training shift')).to_be_visible()
        visit(resident,'/pages/volunteer.html')
        resident.get_by_role('button',name='Claim a slot',exact=True).click()
        expect(resident.get_by_role('button',name='Cancel my signup',exact=True)).to_be_visible()

        visit(staff,'/donation-form/')
        drives = area(staff,'Community supply drives')
        drives.get_by_label('Drive title').fill('Test water drive')
        drives.get_by_label('Requested supplies and delivery instructions').fill('Test delivery at center')
        drives.get_by_label('Unit (e.g. kits, bottles)').fill('bottles')
        drives.get_by_label('Goal quantity').fill('10')
        drives.get_by_role('button',name='Create supply drive',exact=True).click()
        expect(drives.get_by_role('heading',name='Test water drive')).to_be_visible()
        visit(resident,'/donation-form/')
        resident.get_by_label('Quantity (bottles)').fill('4')
        resident.get_by_role('button',name='Pledge supplies',exact=True).click()
        expect(resident.locator('.community-tools')).to_contain_text('4 bottles pledged')
        staff.reload(wait_until='domcontentloaded')
        staff.get_by_role('button',name='Confirm delivery received',exact=True).click()
        expect(staff.locator('.community-tools')).to_contain_text('4 / 10 bottles received (40%)')

        visit(resident,'/pages/preparedness-resources.html')
        language = area(resident,'Preparedness information / Información / Impormasyon')
        language.get_by_label('Language / Idioma / Wika').select_option('es')
        expect(language).to_contain_text('Inundación: Alto')
        language.get_by_label('Neighborhood / Vecindario / Kapitbahayan').select_option(str(nid))
        expect(language).to_contain_text('Zona de evacuación:')
        resident.reload(wait_until='domcontentloaded')
        expect(area(resident,'Preparedness information / Información / Impormasyon').get_by_label('Language / Idioma / Wika')).to_have_value('es')
        language = area(resident,'Preparedness information / Información / Impormasyon')
        language.get_by_label('Language / Idioma / Wika').select_option('tl')
        expect(language).to_contain_text('Baha: Mataas')
        expect(resident.locator('.community-tools')).to_contain_text('Flood preparedness this week')
        feedback = area(resident,'Community FAQ feedback')
        feedback.get_by_label('Search question').fill('water')
        feedback.get_by_role('button',name='Search FAQs',exact=True).click()
        expect(feedback.get_by_role('button',name='Not helpful',exact=True).first).to_be_visible()
        feedback.get_by_role('button',name='Not helpful',exact=True).first.click()
        expect(feedback).to_contain_text('Thank you for your feedback.')
        feedback.get_by_label('Your unanswered question (at least 10 characters)').fill('Where can my household join the next local training?')
        feedback.get_by_role('button',name='Send question to staff',exact=True).click()
        expect(feedback.get_by_role('status').last).to_have_text('Saved.')
        resident.evaluate('''async () => {
            const helper = await import('/assets/js/chatbot/api.js');
            return helper.submitToStaff({name:'Browser resident',email:'resident@example.test',question:'Can PNEC help review my household meeting point?'});
        }''')
        from app.models.faq import UserQuestion
        with app.app_context():
            submitted = UserQuestion.query.filter_by(question_text='Can PNEC help review my household meeting point?').one()
            assert submitted.user_id == accounts['resident']['user']['id'], 'Chatbot lost bearer-authenticated user association'
        visit(staff,'/pages/dashboard.html')
        expect(staff.locator('#questions-table')).to_contain_text('Can PNEC help review my household meeting point?')
        expect(staff.locator('#questions-table')).to_contain_text('Where can my household join the next local training?')
        expect(staff.locator('.community-tools')).to_contain_text('1 not helpful out of 1 votes')
        resident.set_viewport_size({'width':390,'height':844})
        expect(area(resident,'Community FAQ feedback').get_by_role('button',name='Search FAQs',exact=True)).to_be_visible()
        assert not resident.locator('.community-error').count(), 'Community tools reported an error'
        print('PASS: offline/reload checklist recovery, bearer chatbot association, checklist/plan/quiz persistence, check-in/hazard coordination, shift claims, supply receipts, multilingual risk, weekly tips and FAQ/staff queue')
        browser.close()
finally:
    backend.shutdown(); backend.server_close()
    with app.app_context():
        db.session.remove(); db.engine.dispose()
    test_state.cleanup()
