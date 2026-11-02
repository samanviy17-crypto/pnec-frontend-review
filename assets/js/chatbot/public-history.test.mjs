import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('Helper Bot founding history matches approved About page and official PNEC source', () => {
 const prompt=readFileSync(new URL('./prompt.js',import.meta.url),'utf8');
 const about=readFileSync(new URL('../../../pages/about.html',import.meta.url),'utf8');
 assert.match(about,/was established in 2011/);
 assert.match(prompt,/organization established in 2011/);
 assert.doesNotMatch(prompt,/organization founded in (?:1995|2003)/);
});
