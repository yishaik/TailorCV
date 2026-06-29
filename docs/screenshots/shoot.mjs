import { chromium } from 'playwright-core';

const URL = 'https://tailor-cv.yishaik.com';
const OUT = 'D:\\Projects\\TailorCV\\docs\\screenshots';

const JD = `Senior Frontend Engineer

We are looking for a Senior Frontend Engineer to join our product team. You will build and maintain large-scale React applications used by millions of users.

Requirements:
- 5+ years of experience building web applications with React and TypeScript
- Strong knowledge of state management, performance optimization, and component design
- Experience with REST APIs and modern build tooling (Vite, Webpack)
- Familiarity with testing frameworks (Jest, Vitest, Playwright)
- Excellent communication skills and a collaborative mindset

Nice to have:
- Experience with Material UI or design systems
- Exposure to serverless deployment (Vercel, AWS Lambda)
- Mentoring junior engineers`;

const CV = `Jane Doe
Frontend Engineer | jane.doe@example.com | linkedin.com/in/janedoe

Professional Summary
Frontend engineer with 6 years of experience building responsive, high-performance web applications. Passionate about clean UI architecture and developer experience.

Experience

Senior Software Engineer, Acme Corp (2021 - Present)
- Led the migration of a legacy jQuery dashboard to a modern React + TypeScript stack, improving load time by 40%.
- Built a reusable component library adopted by 4 product teams.
- Mentored 3 junior engineers and ran weekly frontend guild sessions.

Software Engineer, Globex (2018 - 2021)
- Developed customer-facing features in React and Redux for a SaaS platform with 200k users.
- Integrated REST APIs and improved test coverage from 35% to 80% using Jest.
- Optimized Webpack build configuration, cutting CI build times in half.

Skills
React, TypeScript, JavaScript, Redux, Jest, Webpack, Vite, HTML, CSS, REST APIs, Git

Education
B.Sc. Computer Science, State University (2014 - 2018)`;

const shot = async (page, name, full = true) => {
  const p = `${OUT}\\${name}.png`;
  await page.screenshot({ path: p, fullPage: full });
  console.log('SAVED', name);
};

(async () => {
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1200 }, deviceScaleFactor: 1 });
  try {
    await page.goto(URL, { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(1500);

    // ---- Step 0: Input ----
    await page.getByPlaceholder(/Paste the job description here/i).fill(JD);
    await page.getByRole('tab', { name: /Paste Text/i }).click();
    await page.getByPlaceholder(/Paste your CV content here/i).fill(CV);
    await page.waitForTimeout(800);
    await shot(page, '01b-input-filled');

    // ---- Step 1: Configure ----
    await page.getByRole('button', { name: /^Continue/i }).click();
    await page.waitForTimeout(1500);
    await shot(page, '02-configure');

    // ---- Trigger pipeline ----
    await page.getByRole('button', { name: /Tailor My CV/i }).click();
    // capture progress dialog quickly
    await page.waitForTimeout(3000);
    try { await shot(page, '03-progress', false); } catch {}

    // ---- Step 2: Results ---- wait until the progress dialog disappears
    await page.getByText(/Tailoring Your CV/i).waitFor({ state: 'hidden', timeout: 240000 });
    await page.getByRole('tab', { name: /Analysis/i }).waitFor({ state: 'visible', timeout: 30000 });
    await page.waitForTimeout(2000);
    await shot(page, '04-results-cv');

    // Switch tabs
    for (const [tab, name] of [
      [/Cover Letter/i, '05-results-cover-letter'],
      [/Analysis/i, '06-results-analysis'],
      [/Changes/i, '07-results-changes'],
    ]) {
      try {
        await page.getByRole('tab', { name: tab }).first().click();
        await page.waitForTimeout(1500);
        await shot(page, name);
      } catch (e) { console.log('skip tab', name, e.message); }
    }
    console.log('ALL DONE');
  } catch (e) {
    console.error('ERROR:', e.message);
    try { await shot(page, 'zz-error-state'); } catch {}
  } finally {
    await browser.close();
  }
})();
