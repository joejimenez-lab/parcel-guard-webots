const fs = require('fs');
const path = require('path');
const {chromium} = require('../demo-studio/node_modules/playwright');
const root = path.resolve(__dirname, '..');
(async () => {
 const browser = await chromium.launch({headless:true});
 try {
  const report = JSON.parse(fs.readFileSync(path.join(root,'results/webots_security.json')));
  const html = fs.readFileSync(path.join(root,'plugins/robot_windows/lockbox_window/lockbox_window.html'),'utf8').replace(/<script type="module">[\s\S]*?<\/script>/g,'');
  fs.mkdirSync(path.join(root,'output/progress2'),{recursive:true});
  const checks=[];
  for (const [state,status] of Object.entries(report.snapshots)) {
   for (const [label,width] of [['desktop',1280],['mobile',390]]) {
    const page=await browser.newPage({viewport:{width,height:1080},deviceScaleFactor:1});
    await page.setContent(html);
    await page.evaluate(s=>window.renderStatus(s),status);
    await page.screenshot({path:path.join(root,`output/progress2/security-${state}-${label}.png`),fullPage:true});
    if(label==='desktop') await page.screenshot({path:path.join(root,`output/progress2/security-${state}-preview.png`)});
    const check=await page.evaluate(()=>({width:innerWidth,body:document.documentElement.scrollWidth,headline:document.querySelector('#headline').textContent,ownerConsole:!document.querySelector('#owner-security').hidden}));
    checks.push({state,label,...check,passed:check.body<=width && check.ownerConsole});
    await page.close();
   }
  }
  const result={passed:checks.every(x=>x.passed),method:'Chromium render of actual owner panel using protected, lockdown and recovered status snapshots from the measured Webots security evaluation; owner signed out',checks};
  fs.writeFileSync(path.join(root,'results/progress2_layout.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
  if(!result.passed)process.exitCode=1;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
