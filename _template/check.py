"""上線前檢查：每一頁都要有 Travelpayouts Drive、AdSense、手動廣告格、GA4 故事事件、og:image、spec-version，sitemap 有收錄、沒有 href="#" 空連結。
作品頁（books／drama／comics 底下）不開自動廣告：AdSense 載入碼不帶 ?client=，連結有 vignette 標記；只有首頁開自動廣告。
舊網址轉址頁（有 meta refresh）不檢查。
用法：在 story-home 資料夾裡執行  python3 _template/check.py
"""
import glob, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKS = {
    'Travelpayouts Drive': 'emrld.ltd/NTc4NjI0.js',
    'AdSense 腳本': 'pagead/js/adsbygoogle.js',
    'GA4': 'G-ZQZHTYTRMQ',
    'GA4 跨子網域': '.knittinghiyori.com',
}
# 故事頁要有標準事件：用共用的 /hy-story.js，或頁面自己寫齊這些事件
STORY_EVENTS = ['story_start', 'story_progress', 'section_view', 'interaction',
                'story_complete', 'cta_click', 'story_exit']
# 刻意不放進 sitemap 的頁面（寫上原因）
SITEMAP_SKIP = {
}
bad = 0
pages = sorted(p for p in glob.glob(os.path.join(ROOT, '**/index.html'), recursive=True)
               if '/_' not in p.replace(ROOT, ''))
sitemap = open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read()
for p in pages:
    rel = os.path.relpath(p, ROOT)
    s = open(p, encoding='utf-8').read()
    if 'http-equiv="refresh"' in s:
        continue  # 舊網址轉址頁
    miss = [k for k, v in CHECKS.items() if v not in s]
    if rel == 'index.html':
        if 'adsbygoogle.js?client=' not in s:
            miss.append('首頁自動廣告（載入碼要帶 ?client=）')
    else:
        if 'adsbygoogle.js?client=' in s:
            miss.append('作品頁不開自動廣告（拿掉載入碼的 ?client=）')
        if 'data-google-vignette' not in s:
            miss.append('vignette 標記')
        if 'name="spec-version"' not in s:
            miss.append('spec-version meta')
        if rel.split('/')[0] not in ('books', 'drama', 'comics'):
            miss.append('要放在 books／drama／comics 類別資料夾裡')
    if rel != 'index.html' and '<ins class="adsbygoogle"' not in s:
        miss.append('手動廣告格')
    if rel != 'index.html' and '/hy-story.js' not in s:
        lack = [e for e in STORY_EVENTS if e not in s]
        if lack:
            miss.append('GA4 故事事件（' + '、'.join(lack) + '）')
    if '/icons/favicon.ico' not in s:
        miss.append('品牌 icon（/icons/favicon.ico）')
    for href in re.findall(r'<link[^>]*rel="(?:icon|apple-touch-icon)"[^>]*href="(/[^"]+)"', s):
        if not os.path.exists(os.path.join(ROOT, href.lstrip('/'))):
            miss.append('icon 檔案不存在（' + href + '）')
    m = re.search(r'property="og:image" content="([^"]*)"', s)
    if not m:
        miss.append('分享預覽圖 og:image')
    else:
        img = m.group(1)
        if not img.startswith('http'):
            miss.append('og:image 不是完整網址（' + img + '）')
        elif img.startswith('https://story.knittinghiyori.com/'):
            local = os.path.join(ROOT, img.split('story.knittinghiyori.com/', 1)[1])
            if not os.path.exists(local):
                miss.append('og:image 檔案不存在（' + img + '）')
    url = 'https://story.knittinghiyori.com/' + os.path.dirname(rel) + ('/' if os.path.dirname(rel) else '')
    if rel.count('/') == 2 and rel not in SITEMAP_SKIP and url not in sitemap:
        miss.append('sitemap 沒有這頁')
    live_lines = [l for l in s.splitlines() if not l.lstrip().startswith('//')]
    if any('href="#"' in l for l in live_lines):
        miss.append('有 href="#" 空連結')
    print(('✅ ' if not miss else '❌ ') + rel + ('' if not miss else '　缺：' + '、'.join(miss)))
    bad += bool(miss)
print(f'\n共 {len(pages)} 頁，{bad} 頁有問題')
sys.exit(1 if bad else 0)
