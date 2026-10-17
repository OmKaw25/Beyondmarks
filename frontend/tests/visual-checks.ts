import {expect,type Page} from '@playwright/test';

export async function captureLayouts(page:Page,name:string,fullPage=true){
  await expect(page.getByRole('status',{name:'Loading',exact:true})).toHaveCount(0);
  if(await page.locator('.app-layout').count())await expect(page.getByRole('button',{name:'Sign out',exact:true})).toBeVisible();
  for(const viewport of [{width:1440,height:1000},{width:390,height:844}]){
    await page.setViewportSize(viewport);
    for(const theme of ['light','dark']){
      const target=page.getByRole('button',{name:`Switch to ${theme} theme`});
      if(await target.count())await target.click();
      await expect(page.getByRole('heading',{level:1})).toBeVisible();
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
      await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
      await page.screenshot({path:`../docs/screenshots/${name}-${viewport.width}-${theme}.png`,fullPage,animations:'disabled'});
    }
  }
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('button',{name:'Switch to light theme'}).click();
}
