const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PROGRAMS = [
    ["001Do00000ScUyCIAV", "AA in Business", "https://www.uagc.edu/online-degrees/associate/business"],
    ["001Do00000ScUzUIAV", "AA in Early Childhood Education", "https://www.uagc.edu/online-degrees/associate/early-childhood-education"],
    ["001Do00000ScUyvIAF", "AA in Military Studies", "https://www.uagc.edu/online-degrees/associate/military-studies"],
    ["001Do00000ScUyDIAV", "AA in Organizational Management", "https://www.uagc.edu/online-degrees/associate/organizational-management"],
    ["001Do00000ScUyPIAV", "BA in Accounting", "https://www.uagc.edu/online-degrees/bachelors/accounting"],
    ["001Do00000ScUzGIAV", "BA in Applied Behavioral Science", "https://www.uagc.edu/online-degrees/bachelors/applied-behavioral-science"],
    ["001Do00000ScUyQIAV", "BA in Business Administration", "https://www.uagc.edu/online-degrees/bachelors/business-administration"],
    ["001Do00000ScUyEIAV", "BA in Business Economics", "https://www.uagc.edu/online-degrees/bachelors/business-economics"],
    ["001Do00000ScUzHIAV", "BA in Business Information Systems", "https://www.uagc.edu/online-degrees/bachelors/business-information-systems"],
    ["001Do00000ScUyRIAV", "BA in Business Leadership", "https://www.uagc.edu/online-degrees/bachelors/business-leadership"],
    ["001Do00000ScUzdIAF", "BA in Child Development", "https://www.uagc.edu/online-degrees/bachelors/child-development"],
    ["001Do00000ScUysIAF", "BA in Communication Studies", "https://www.uagc.edu/online-degrees/bachelors/communication-studies"],
    ["001Do00000ScUzeIAF", "BA in ECD w/ Diff Instruction", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-development-differentiated-instruction"],
    ["001Do00000ScUzfIAF", "BA in Early Childhood Education", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-education"],
    ["001Do00000ScUzgIAF", "BA in ECE Administration", "https://www.uagc.edu/online-degrees/bachelors/early-childhood-education-administration"],
    ["001Do00000ScUzhIAF", "BA in Education Studies", "https://www.uagc.edu/online-degrees/bachelors/education-studies"],
    ["001Do00000ScUySIAV", "BA in Finance", "https://www.uagc.edu/online-degrees/bachelors/finance"],
    ["001Do00000ScUzEIAV", "BA in Health & Human Services", "https://www.uagc.edu/online-degrees/bachelors/health-human-services"],
    ["001Do00000ScUyeIAF", "BA in Health and Wellness", "https://www.uagc.edu/online-degrees/bachelors/health-and-wellness"],
    ["001Do00000ScUybIAF", "BA in Health Care Administration", "https://www.uagc.edu/online-degrees/bachelors/health-care-administration"],
    ["001Do00000ScUz6IAF", "BA in Homeland Security & EM", "https://www.uagc.edu/online-degrees/bachelors/homeland-security-emergency-management"],
    ["001Do00000ScUyXIAV", "BA in Human Resources Mgmt", "https://www.uagc.edu/online-degrees/bachelors/human-resources-management"],
    ["001Do00000ScUzZIAV", "BA in Instructional Design", "https://www.uagc.edu/online-degrees/bachelors/instructional-design"],
    ["001Do00000ScUyqIAF", "BA in Liberal Arts", "https://www.uagc.edu/online-degrees/bachelors/liberal-arts"],
    ["001Do00000ScUyTIAV", "BA in Marketing", "https://www.uagc.edu/online-degrees/bachelors/marketing"],
    ["001Do00000ScUyUIAV", "BA in Operations Mgmt & Analysis", "https://www.uagc.edu/online-degrees/bachelors/operations-management-analysis"],
    ["001Do00000ScUyVIAV", "BA in Organizational Management", "https://www.uagc.edu/online-degrees/bachelors/organizational-management"],
    ["001Do00000ScUyWIAV", "BA in Project Management", "https://www.uagc.edu/online-degrees/bachelors/project-management"],
    ["001Do00000ScUzFIAV", "BA in Psychology", "https://www.uagc.edu/online-degrees/bachelors/psychology"],
    ["001Do00000ScUz7IAF", "BA in Social and Criminal Justice", "https://www.uagc.edu/online-degrees/bachelors/criminal-justice"],
    ["001Do00000ScUyzIAF", "BA in Social Science", "https://www.uagc.edu/online-degrees/bachelors/social-science"],
    ["001Do00000ScUzCIAV", "BA in Sociology", "https://www.uagc.edu/online-degrees/bachelors/sociology"],
    ["001Do00000ScUyNIAV", "BA in Supply Chain Management", "https://www.uagc.edu/online-degrees/bachelors/supply-chain-management"],
    ["001Do00000ScUzIIAV", "BS in Computer Software Tech", "https://www.uagc.edu/online-degrees/bachelors/computer-software-technology"],
    ["001Do00000ScUzJIAV", "BS in Cyber & Data Security", "https://www.uagc.edu/online-degrees/bachelors/cyber-data-security-technology"],
    ["001Do00000ScUyaIAF", "BS in Health Info Management", "https://www.uagc.edu/online-degrees/bachelors/health-information-management"],
    ["001Do00000ScUzKIAV", "BS in Information Technology", "https://www.uagc.edu/online-degrees/bachelors/information-technology"],
    ["001Do00000ScUymIAF", "BS in Nursing", "https://www.uagc.edu/online-degrees/bachelors/nursing"],
    ["001Vr00000YtotRIAR", "DPS in Org Leadership", "https://www.uagc.edu/online-degrees/doctoral/organizational-leadership"],
    ["001Do00000ScUzbIAF", "MA in ECE Leadership", "https://www.uagc.edu/online-degrees/masters/early-childhood-education-leadership"],
    ["001Do00000ScUzcIAF", "MA in Education", "https://www.uagc.edu/online-degrees/masters/education"],
    ["001Do00000ScUynIAF", "MA in Health Care Admin", "https://www.uagc.edu/online-degrees/masters/health-care-administration"],
    ["001Do00000ScUzAIAV", "MA in Human Services", "https://www.uagc.edu/online-degrees/masters/human-services"],
    ["001Do00000ScUy8IAF", "MA in Organizational Mgmt", "https://www.uagc.edu/online-degrees/masters/organizational-management"],
    ["001Do00000ScUz9IAF", "MA in Psychology", "https://www.uagc.edu/online-degrees/masters/psychology"],
    ["001Do00000ScUzSIAV", "MA in Special Education", "https://www.uagc.edu/online-degrees/masters/special-education"],
    ["001Do00000ScUzTIAV", "MA in Teaching & Learning w/ Tech", "https://www.uagc.edu/online-degrees/masters/teaching-and-learning-with-technology"],
    ["001Do00000ScUyZIAV", "Master of Accountancy", "https://www.uagc.edu/online-degrees/masters/accounting"],
    ["001Do00000ScUy9IAF", "MBA", "https://www.uagc.edu/online-degrees/masters/business-administration"],
    ["001Do00000ScUyAIAV", "Master of HR Management", "https://www.uagc.edu/online-degrees/masters/human-resources-management"],
    ["001Do00000ScUzMIAV", "Master of ISM", "https://www.uagc.edu/online-degrees/masters/information-systems-management"],
    ["001Do00000ScUylIAF", "Master of Public Health", "https://www.uagc.edu/online-degrees/masters/public-health"],
    ["001Vr00000t9K7vIAE", "MPS in Leadership", "https://www.uagc.edu/online-degrees/masters/leadership"],
    ["001Do00000ScUz8IAF", "MS in Criminal Justice", "https://www.uagc.edu/online-degrees/masters/criminal-justice"],
    ["001Do00000ScUyBIAV", "MS in Finance", "https://www.uagc.edu/online-degrees/masters/finance"],
    ["001Do00000ScUykIAF", "MS in Health Informatics", "https://www.uagc.edu/online-degrees/masters/health-informatics-analytics"],
    ["001Do00000ScUzQIAV", "MS in Instructional Design & Tech", "https://www.uagc.edu/online-degrees/masters/instructional-design-technology"],
    ["001Do00000ScUzNIAV", "MS in Technology Management", "https://www.uagc.edu/online-degrees/masters/technology-management"],
    ["001Do00000ScUzOIAV", "Post Bacc Teaching Cert", "https://www.uagc.edu/online-degrees/certificates/post-baccalaureate-teaching"],
    ["001Do00000YZZzVIAX", "Undecided - Bachelors", "https://www.uagc.edu/online-degrees/bachelors"],
    ["001Do00000YZZxZIAX", "Undecided - Business", "https://www.uagc.edu/online-degrees/business"],
    ["001Do00000YZZxjIAH", "Undecided - Criminal Justice", "https://www.uagc.edu/online-degrees/criminal-justice"],
    ["001Do00000YZZyXIAX", "Undecided - Education", "https://www.uagc.edu/online-degrees/education"],
    ["001Do00000YZZyYIAX", "Undecided - Health Care", "https://www.uagc.edu/online-degrees/health-care"],
    ["001Do00000YZZymIAH", "Undecided - Information Technology", "https://www.uagc.edu/online-degrees/information-technology"],
    ["001Do00000YZZz6IAH", "Undecided - Liberal Arts", "https://www.uagc.edu/online-degrees/liberal-arts"],
    ["001Do00000YZZz7IAH", "Undecided - Masters", "https://www.uagc.edu/online-degrees/masters"],
    ["001Do00000YZZzGIAX", "Undecided - Social & Behavioral Science", "https://www.uagc.edu/online-degrees/social-behavioral-science"],
    ["001Do00000YZZzHIAX", "Undecided - Undecided", "https://www.uagc.edu/online-degrees"],
];

const OUTPUT_DIR = 'C:/Users/kseaman/Downloads/Cursor/screenshots';

async function main() {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    const manifest = {};
    
    const browser = await chromium.launch({ headless: true });

    // Desktop screenshots
    console.log(`=== DESKTOP (${PROGRAMS.length} programs) ===`);
    const desktopCtx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const desktopPage = await desktopCtx.newPage();

    for (let i = 0; i < PROGRAMS.length; i++) {
        const [pid, name, url] = PROGRAMS[i];
        process.stdout.write(`  [${i+1}/${PROGRAMS.length}] ${name}... `);
        try {
            await desktopPage.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
            await desktopPage.waitForTimeout(1000);
            const fname = `desktop_${pid}.png`;
            await desktopPage.screenshot({ path: path.join(OUTPUT_DIR, fname) });
            manifest[pid] = manifest[pid] || {};
            manifest[pid].desktop = fname;
            console.log('OK');
        } catch (e) {
            console.log(`ERROR: ${e.message.slice(0, 60)}`);
            manifest[pid] = manifest[pid] || {};
            manifest[pid].desktop = null;
        }
    }
    await desktopCtx.close();

    // Mobile screenshots (extended scroll)
    console.log(`\n=== MOBILE (${PROGRAMS.length} programs) ===`);
    const mobileCtx = await browser.newContext({ 
        viewport: { width: 390, height: 844 },
        isMobile: true,
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1'
    });
    const mobilePage = await mobileCtx.newPage();

    for (let i = 0; i < PROGRAMS.length; i++) {
        const [pid, name, url] = PROGRAMS[i];
        process.stdout.write(`  [${i+1}/${PROGRAMS.length}] ${name}... `);
        try {
            await mobilePage.goto(url, { waitUntil: 'networkidle', timeout: 25000 });
            await mobilePage.waitForTimeout(1000);
            const fname = `mobile_${pid}.png`;
            await mobilePage.screenshot({ 
                path: path.join(OUTPUT_DIR, fname),
                clip: { x: 0, y: 0, width: 390, height: 2000 }
            });
            manifest[pid] = manifest[pid] || {};
            manifest[pid].mobile = fname;
            console.log('OK');
        } catch (e) {
            console.log(`ERROR: ${e.message.slice(0, 60)}`);
            manifest[pid] = manifest[pid] || {};
            manifest[pid].mobile = null;
        }
    }
    await mobileCtx.close();
    await browser.close();

    fs.writeFileSync(path.join(OUTPUT_DIR, 'manifest.json'), JSON.stringify(manifest, null, 2));
    const success = Object.values(manifest).filter(v => v.desktop).length;
    console.log(`\nDone! ${success}/${PROGRAMS.length} programs captured (desktop + mobile).`);
}

main().catch(e => { console.error(e); process.exit(1); });
