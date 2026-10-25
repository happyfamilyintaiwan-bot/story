"""追劇日曆計算機：改完 dramas.json 或頁面文字後跑一次。
1. 三語頁「目前收錄的劇」清單（爬蟲不跑 JS 也讀得到）
2. FAQ 的 JSON-LD（從頁面 .dc-faq 逐字抓，保證一致）
3. 標題字型的 &text= 子集（只載用到的字）
4. story 首頁「追劇日曆」區的劇清單（播出中、即將開播的前 4 部）
用法：在 story 資料夾執行  python3 drama/calendar/_tools/sync.py
（_tools 底線開頭，GitHub Pages 不會公開）
"""
import html, json, os, re, urllib.parse

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://story.knittinghiyori.com/drama/calendar/'
PAGES = {'zh': ('index.html', ''), 'en': ('en/index.html', 'en/'), 'ja': ('ja/index.html', 'ja/')}
FONT = {'zh': 'Noto+Serif+TC', 'en': 'Noto+Serif+TC', 'ja': 'Noto+Serif+JP'}
STATUS = {
    'zh': {'airing': '播出中', 'upcoming': '即將開播', 'ended': '已完結'},
    'en': {'airing': 'airing', 'upcoming': 'coming soon', 'ended': 'finished'},
    'ja': {'airing': '配信中', 'upcoming': '配信予定', 'ended': '配信終了'},
}
ART = {'zh': '追劇日曆文章', 'en': 'guide', 'ja': '記事'}
ORDER = {'airing': 0, 'upcoming': 1, 'ended': 2}

data = json.load(open(os.path.join(HERE, 'dramas.json'), encoding='utf-8'))


def put(s, name, inner):
    pat = re.compile(r'(<!--%s:start-->)[\s\S]*?(<!--%s:end-->)' % (name, name))
    if not pat.search(s):
        raise SystemExit('找不到標記 ' + name)
    return pat.sub(lambda m: m.group(1) + inner + m.group(2), s)


def text(fragment):
    return html.unescape(re.sub(r'<[^>]+>', '', fragment)).strip()


for lang, (path, prefix) in PAGES.items():
    p = os.path.join(HERE, path)
    s = open(p, encoding='utf-8').read()

    items = []
    for d in sorted(data['dramas'], key=lambda d: ORDER.get(d.get('status'), 0)):
        t = d['title'].get(lang) or d['title']['zh']
        url = BASE + prefix + '?d=' + d['id']
        li = '<li><a href="%s" data-cta="dc_list_%s">%s</a>（%s）' % (url, d['id'], html.escape(t), STATUS[lang].get(d.get('status'), ''))
        art = (d.get('articles') or {}).get(lang)
        if art:
            li += '・<a href="%s" data-cta="dc_article_%s">%s</a>' % (art, d['id'], ART[lang])
        items.append(li + '</li>')
    s = put(s, 'dc-list', '\n<ul class="dc-list">\n' + '\n'.join(items) + '\n</ul>\n')

    faq_block = re.search(r'<section[^>]*class="dc-faq"[\s\S]*?</section>', s).group(0)
    qa = re.findall(r'<details><summary>([\s\S]*?)</summary><p>([\s\S]*?)</p></details>', faq_block)
    ld = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': text(q), 'acceptedAnswer': {'@type': 'Answer', 'text': text(a)}} for q, a in qa]}
    s = put(s, 'dc-faq-ld', '\n<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False) + '\n</script>\n')

    heads = ''.join(text(h) for h in re.findall(r'<h[12][^>]*>([\s\S]*?)</h[12]>', s))
    heads += ''.join(d['title'].get(lang) or d['title']['zh'] for d in data['dramas'])
    chars = ''.join(sorted(set(heads) - set(' \n')))
    href = 'https://fonts.googleapis.com/css2?family=%s:wght@900&display=swap&text=%s' % (FONT[lang], urllib.parse.quote(chars))
    s = put(s, 'dc-font', '<link rel="stylesheet" href="%s">' % html.escape(href))

    open(p, 'w', encoding='utf-8').write(s)
    print('✅', path, '劇', len(items), '部、FAQ', len(qa), '題、字型', len(chars), '字')

# story 首頁（hub）追劇日曆區
ROOT = os.path.dirname(os.path.dirname(HERE))
hub = os.path.join(ROOT, 'index.html')
s = open(hub, encoding='utf-8').read()
STAT = {'airing': '播出中', 'upcoming': '即將開播', 'ended': '已完結'}
live = [d for d in sorted(data['dramas'], key=lambda d: ORDER.get(d.get('status'), 0)) if d.get('status') != 'ended'][:4]
lis = []
for d in live:
    lis.append('<li><a href="%s?d=%s" data-cta="home_calendar_%s" data-cta-type="story"><strong>%s</strong><span data-dc-home="%s">%s・全 %d 集</span><span class="dc-h-fin"></span></a></li>' % (
        BASE, d['id'], d['id'], html.escape(d['title']['zh']), d['id'], STAT.get(d.get('status'), ''), d['episodes']))
s = put(s, 'dc-home', '\n    <ul>\n      ' + '\n      '.join(lis) + '\n    </ul>\n    ')
open(hub, 'w', encoding='utf-8').write(s)
print('✅ story 首頁追劇日曆', len(lis), '部')
