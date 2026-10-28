"""《歡迎回來，初戀。》日文版、英文版產生器。

中文版 ../index.html 是母版：CSS、翻面卡 JS、每張卡的圖片檔名與日文台詞都從中文版讀，
這裡只放日文、英文的文字。每播一集的同步流程：
  1. 照舊在中文版加卡片（data-card 代碼、圖片、日文台詞）
  2. 在下面 CARDS 補上新卡的 ja／en 文字，EPISODES 補集名，STATUS 改播出進度；
     T 裡 ja／en 的 status、later、title、desc、note（第幾集、下一集日期）跟著改
  3. 在 story 根目錄執行  python3 drama/welcome-back-first-love/_tools/build_i18n.py
  4. 跑 python3 _template/check.py
少了哪張卡的翻譯，執行時會直接報錯，不會產生缺卡的頁面。
"""
import html, json, os, re, sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
BASE = 'https://story.knittinghiyori.com/drama/welcome-back-first-love/'
ASSET = '/assets/welcome-back-first-love/'

zh = open(os.path.join(WORK, 'index.html'), encoding='utf-8').read()
STYLE = re.search(r'<style>.*?</style>', zh, re.S).group(0)
FLIP_JS = re.search(r'<script>\n\(function \(\) \{\n  var cards.*?</script>', zh, re.S).group(0)
SPEC = re.search(r'<meta name="spec-version" content="([^"]+)">', zh).group(1)

# 從中文版讀出：哪一集有哪些卡、每面的圖片與日文台詞
ZH_EPS = []
for ep_block in re.split(r'<p class="wb-ep">', zh)[1:]:
    cards = []
    for code, body in re.findall(r'<article class="wb-card" data-card="([a-z0-9_]+)">(.*?)</article>', ep_block, re.S):
        faces = []
        for face in re.findall(r'<div class="wb-face wb-(?:front|back)">(.*?)<button', body, re.S):
            faces.append({
                'imgs': re.findall(r'src="' + re.escape(ASSET) + r'([^"]+)"', face),
                'quote': re.search(r'<p class="wb-q" lang="ja"><span>(.*?)</span>', face).group(1),
            })
        cards.append((code, faces))
    ZH_EPS.append(cards)

# ---- 播出進度（每集更新） ----
STATUS = {'aired': 3, 'total': 8}

EPISODES = {
    'ja': ['金髪ヤンキーと10年ぶりの再会', '10年越しの秘めた想い', '「好き」の正体'],
    'en': ['A blond delinquent, reunited after 10 years', 'Feelings hidden for 10 years', 'What “like” really means'],
}

# 每張卡：topic、front／back 的 scene、alt（一張圖一個）、en 的台詞翻譯 tr
CARDS = {
    'ice': {
        'ja': {'topic': 'アイス',
               'front': {'scene': '授業中、田口が急に「アイス食べたい」と言い出す。この時間は購買も開いてないよ、と詩織が言うと、少し考えて：',
                         'alt': ['おかえり、初恋。第1話の高校時代の回想、山根詩織にアイスを手渡す田口涼介']},
               'back': {'scene': '10年後の暑い日、会社でアイスが配られる。受け取った瞬間、また彼のことを思い出す。',
                        'alt': ['おかえり、初恋。第1話、暑い日のオフィスで主任からアイスを受け取る山根詩織']}},
        'en': {'topic': 'Ice pop',
               'front': {'scene': 'In the middle of class, Taguchi suddenly says he wants an ice pop. When Shiori says the school shop won’t be open now, he thinks for a second:',
                         'tr': 'Then let’s sneak out.',
                         'alt': ['Welcome Back, First Love Episode 1, high school flashback: Ryosuke Taguchi hands Shiori Yamane an ice pop']},
               'back': {'scene': 'Ten years later, on a hot day, her office hands out ice pops. The moment she takes one, she thinks of him again.',
                        'tr': 'It comes back to me in unguarded moments.',
                        'alt': ['Welcome Back, First Love Episode 1: on a hot day at the office, Shiori Yamane takes an ice pop from her manager']}},
    },
    'seat': {
        'ja': {'topic': 'となりに座る',
               'front': {'scene': 'クラスに居場所がなく、人のいない場所に逃げた詩織。そこを陣取っていたのは金髪の田口だった。みんなになじめないと話す彼女に、彼は：',
                         'alt': ['おかえり、初恋。第1話の高校時代の回想、人のいない一角に並んで座る金髪の田口涼介と山根詩織']},
               'back': {'scene': '10年後の同窓会、彼女はまた隅でひとり座っている。彼が近づいてきて、ひとこと：',
                        'alt': ['おかえり、初恋。第1話、同窓会で山根詩織の隣に座る田口涼介。10年ぶりに並んで座る2人']}},
        'en': {'topic': 'Side by side',
               'front': {'scene': 'Unable to fit in with her class, Shiori escapes to an empty spot and finds blond Taguchi already claiming it. When she says she can’t fit in with everyone, he says:',
                         'tr': 'Then you’re just like me.',
                         'alt': ['Welcome Back, First Love Episode 1, high school flashback: blond Ryosuke Taguchi and Shiori Yamane sitting side by side in an empty corner']},
               'back': {'scene': 'At the reunion ten years later, she’s sitting alone in a corner again. He walks over and asks:',
                        'tr': 'Mind if I sit here?',
                        'alt': ['Welcome Back, First Love Episode 1: at the class reunion, Ryosuke Taguchi sits down next to Shiori Yamane, side by side again ten years later']}},
    },
    'ear': {
        'ja': {'topic': 'ピアスの穴',
               'front': {'scene': '初めて話しかけたとき、彼女はピアスが素敵だと言った。「触ってみる？」と聞かれて、慌てて遠慮する。',
                         'alt': ['おかえり、初恋。第1話の高校時代の回想、自分のピアスに触れる金髪の田口涼介と、そばに立つ山根詩織']},
               'back': {'scene': '髪を黒く染め、ピアスも外した彼。でも、ピアスの穴は残っていた。今度は、彼女が本当に手を伸ばして触れる。',
                        'alt': ['おかえり、初恋。第1話、田口涼介のピアスの穴に手を伸ばす山根詩織']}},
        'en': {'topic': 'Ear piercing',
               'front': {'scene': 'The first time they talk, she tells him his earrings look nice. He asks if she wants to touch them; flustered, she says she couldn’t.',
                         'tr': 'They suit you. I think they look lovely.',
                         'alt': ['Welcome Back, First Love Episode 1, high school flashback: blond Ryosuke Taguchi touches his earring while Shiori Yamane stands beside him']},
               'back': {'scene': 'He’s dyed his hair black and taken out the earrings, but the piercing holes are still there. This time, she really does reach out and touch.',
                        'tr': 'Welcome back, Taguchi.',
                        'alt': ['Welcome Back, First Love Episode 1: Shiori Yamane reaches out to touch Ryosuke Taguchi’s ear piercing']}},
    },
    'again': {
        'ja': {'topic': 'もう一度',
               'front': {'scene': '2人で教室を抜け出してアイスを食べ、笑って別れる前に、彼が何気なく言う：',
                         'alt': ['おかえり、初恋。第1話の高校時代の回想、学校を抜け出して草むらの横を歩く金髪の田口涼介と山根詩織',
                                 'おかえり、初恋。第1話の高校時代の回想、夕日の中で笑い合う金髪の田口涼介と山根詩織']},
               'back': {'scene': '10年後、今度は彼女が勇気を出して、また仲良くなれるかと聞く。彼は近づいてきて、思っていたより少しだけ多い答えをくれる：',
                        'alt': ['おかえり、初恋。第1話、山根詩織に顔を近づける田口涼介',
                                'おかえり、初恋。第1話、夜に見つめ合う田口涼介と山根詩織']}},
        'en': {'topic': 'Once more',
               'front': {'scene': 'After sneaking out of class together for ice pops, just before they part laughing, he says casually:',
                         'tr': 'Let’s sneak out again sometime.',
                         'alt': ['Welcome Back, First Love Episode 1, high school flashback: blond Ryosuke Taguchi and Shiori Yamane walk past the grass after sneaking out of school',
                                 'Welcome Back, First Love Episode 1, high school flashback: blond Ryosuke Taguchi and Shiori Yamane smile at each other at sunset']},
               'back': {'scene': 'Ten years later, it’s her turn to work up the courage and ask if they can be close again. He leans in, and his answer is a little more than she expected:',
                        'tr': 'As more than friends.',
                        'alt': ['Welcome Back, First Love Episode 1: Ryosuke Taguchi leans in close to Shiori Yamane',
                                'Welcome Back, First Love Episode 1: Ryosuke Taguchi and Shiori Yamane look at each other at night']}},
    },
    'lunch': {
        'ja': {'topic': 'お昼ごはん',
               'front': {'scene': '高校の昼休み、小さなお弁当を見て足りるのかと聞き、コンビニのパンを差し出す彼：',
                         'alt': ['おかえり、初恋。第2話の高校時代の回想、山根詩織にパンを分ける田口涼介']},
               'back': {'scene': '10年後、一緒にお昼を食べると、彼は同じことを聞いて、自分のおかずを彼女の口に運ぶ：',
                        'alt': ['おかえり、初恋。第2話、10年後に山根詩織におかずを食べさせる田口涼介']}},
        'en': {'topic': 'Lunch',
               'front': {'scene': 'At lunch in high school, he looks at her tiny bento, asks if it’s enough, and hands her a bread roll from the convenience store:',
                         'tr': 'Hey, is that little bento really enough?',
                         'alt': ['Welcome Back, First Love Episode 2, high school flashback: Ryosuke Taguchi shares his bread with Shiori Yamane']},
               'back': {'scene': 'Ten years later, at lunch together, he asks the same thing, then feeds her a bite from his own plate:',
                        'tr': 'Still eating just that much?',
                        'alt': ['Welcome Back, First Love Episode 2: ten years later, Ryosuke Taguchi feeds Shiori Yamane a bite of his food']}},
    },
    'book': {
        'ja': {'topic': '本',
               'front': {'scene': '好きな小説の話をしているうちに、うっかりネタバレしてしまい、慌てて謝る彼女。彼は：',
                         'alt': ['おかえり、初恋。第2話の高校時代の回想、手の中で開かれた小説']},
               'back': {'scene': '10年後、彼が取り出したのは、同じシリーズの新刊だった：',
                        'alt': ['おかえり、初恋。第2話、小説の新刊を手にした眼鏡姿の田口涼介']}},
        'en': {'topic': 'The book',
               'front': {'scene': 'Telling him about a novel she loves, she accidentally spoils it and hurries to apologize. He says:',
                         'tr': 'It’s easier to read once you’ve told me about it like that.',
                         'alt': ['Welcome Back, First Love Episode 2, high school flashback: a novel held open in someone’s hands']},
               'back': {'scene': 'Ten years later, he pulls out the newest volume of the same series:',
                        'tr': 'You’re the reason I started reading, Yamane.',
                        'alt': ['Welcome Back, First Love Episode 2: Ryosuke Taguchi, wearing glasses, holds the new volume of the novel']}},
    },
    'chara': {
        'ja': {'topic': '彼に似たキャラ',
               'front': {'scene': '小説でいちばん好きなキャラが、ちょっと田口に似ていると話す彼女。どこが好きか言おうとすると、彼が照れてさえぎる：',
                         'alt': ['おかえり、初恋。第2話の高校時代の回想、ベンチに並んで座って本を読む田口涼介と山根詩織']},
               'back': {'scene': '10年後、今度は彼のほうから聞いてくる。彼女は顔を赤くして、言葉が出てこない：',
                        'alt': ['おかえり、初恋。第2話、好きなキャラのどこが好きかと聞かれて照れ笑いする山根詩織']}},
        'en': {'topic': 'The character like him',
               'front': {'scene': 'She says her favorite character in the novel is a bit like Taguchi. As she starts to explain what she likes about him, he cuts in, embarrassed:',
                         'tr': 'That’s kinda embarrassing. You don’t have to say.',
                         'alt': ['Welcome Back, First Love Episode 2, high school flashback: Ryosuke Taguchi and Shiori Yamane read side by side on a bench']},
               'back': {'scene': 'Ten years later, he’s the one who asks. She blushes and can’t get the words out:',
                        'tr': 'So what was it you liked about him?',
                        'alt': ['Welcome Back, First Love Episode 2: asked what she likes about the character, Shiori Yamane smiles shyly']}},
    },
    'tomorrow': {
        'ja': {'topic': 'また明日',
               'front': {'scene': '昼休みが終わる頃、放課後もたぶんここにいると言って、彼はひとこと残していく：',
                         'alt': ['おかえり、初恋。第2話の高校時代の回想、昼休みの終わりに別れる田口涼介と山根詩織']},
               'back': {'scene': '10年後の夜、会社で彼を待っていた彼女は、ずっと胸にしまっていた気持ちを打ち明ける：',
                        'alt': ['おかえり、初恋。第2話、夜、山根詩織の本音を聞く田口涼介']}},
        'en': {'topic': 'See you tomorrow',
               'front': {'scene': 'As lunch break ends, he says he’ll probably be here after school too, and leaves her with:',
                         'tr': 'See you tomorrow.',
                         'alt': ['Welcome Back, First Love Episode 2, high school flashback: Ryosuke Taguchi and Shiori Yamane say goodbye as lunch break ends']},
               'back': {'scene': 'One night ten years later, she waits for him at the office and tells him what she’s kept inside for so long:',
                        'tr': 'I’m so happy I get to say “see you tomorrow” again.',
                        'alt': ['Welcome Back, First Love Episode 2: at night, Ryosuke Taguchi listens as Shiori Yamane opens up']}},
    },
    'leave': {
        'ja': {'topic': '離れる',
               'front': {'scene': '高校時代、彼は冷たく言い放ったことがある：',
                         'alt': ['おかえり、初恋。第3話の高校時代の回想、金髪の田口涼介']},
               'back': {'scene': '10年後に告白されても、なかなか返事ができない彼女。ようやく、心の中の怖さを口にする：',
                        'alt': ['おかえり、初恋。第3話、田口とはもう離れたくないと先輩に打ち明ける山根詩織']}},
        'en': {'topic': 'Apart',
               'front': {'scene': 'Back in high school, he once told her coldly:',
                         'tr': 'Don’t talk to me anymore.',
                         'alt': ['Welcome Back, First Love Episode 3, high school flashback: blond Ryosuke Taguchi']},
               'back': {'scene': 'Ten years later, he confesses, but she can’t bring herself to answer. At last she says what she’s afraid of:',
                        'tr': 'I don’t want us to be apart again.',
                        'alt': ['Welcome Back, First Love Episode 3: Shiori Yamane tells a senior colleague she never wants to be apart from Taguchi again']}},
    },
    'bite': {
        'ja': {'topic': 'ひとくち',
               'front': {'scene': '高校時代、2人で分け合って食べながら、大事なのは誰かがいることじゃない、と彼は言う：',
                         'alt': ['おかえり、初恋。第3話の高校時代の回想、一緒に食べる山根詩織と田口涼介']},
               'back': {'scene': '10年後のデート、彼女がひとくち分けると、彼は昔も同じことがあったのを思い出す：',
                        'alt': ['おかえり、初恋。第3話のデート、山根詩織に分けてもらった料理を食べる田口涼介']}},
        'en': {'topic': 'One bite',
               'front': {'scene': 'Sharing food in high school, he says the point isn’t just having someone there:',
                         'tr': 'It’s not about eating with someone. It’s about who you eat with.',
                         'alt': ['Welcome Back, First Love Episode 3, high school flashback: Shiori Yamane and Ryosuke Taguchi eat together']},
               'back': {'scene': 'On a date ten years later, she gives him a bite, and he remembers this happened before:',
                        'tr': 'Food tastes good when I eat with you, Yamane.',
                        'alt': ['Welcome Back, First Love Episode 3, on a date: Ryosuke Taguchi eats the food Shiori Yamane shared with him']}},
    },
    'hand': {
        'ja': {'topic': '手をつなぐ',
               'front': {'scene': '高校の夏祭り、2人は一度だけ手をつないだ。その夜、分かれ道まで来ると、彼女は手を振って：',
                         'alt': ['おかえり、初恋。第3話の高校時代の回想、夏祭りの夜、提灯の下の夜道を歩く金髪の田口涼介と山根詩織',
                                 'おかえり、初恋。第3話の高校時代の回想、祭りの夜に田口涼介へ手を振って別れる山根詩織']},
               'back': {'scene': '10年後、祭りで手をつないだあの時はすごくドキドキしていた、と彼は話す。デート中に声をかけられると、今度は彼女のほうから手をつなぐ：',
                        'alt': ['おかえり、初恋。第3話、並んで座り、高校の祭りで手をつないだ思い出を話す田口涼介と山根詩織',
                                'おかえり、初恋。第3話のデート、田口涼介の手を取る山根詩織']}},
        'en': {'topic': 'Holding hands',
               'front': {'scene': 'At a summer festival in high school, they held hands once. That night, when they reach the fork in the road, she waves and says:',
                         'tr': 'I go this way. See you at school.',
                         'alt': ['Welcome Back, First Love Episode 3, high school flashback: on the festival night, blond Ryosuke Taguchi and Shiori Yamane walk down a lantern-lit street',
                                 'Welcome Back, First Love Episode 3, high school flashback: Shiori Yamane waves goodbye to Ryosuke Taguchi after the festival']},
               'back': {'scene': 'Ten years later, he admits his heart was racing when they held hands at the festival. On their date, when someone tries to chat them up, this time she’s the one who takes his hand:',
                        'tr': 'This way, nobody will try to talk to us again, right?',
                        'alt': ['Welcome Back, First Love Episode 3: sitting side by side, Ryosuke Taguchi and Shiori Yamane talk about holding hands at the festival in high school',
                                'Welcome Back, First Love Episode 3, on a date: Shiori Yamane takes Ryosuke Taguchi’s hand']}},
    },
    'like': {
        'ja': {'topic': '好き',
               'front': {'scene': '高校の祭りの夜、彼のとなりを歩きながら、彼女が心の中で思っていたこと：',
                         'alt': ['おかえり、初恋。第3話の高校時代の回想、祭りの夜、田口涼介のとなりを歩く山根詩織']},
               'back': {'scene': '10年後、彼女はその気持ちに名前をつけて、声に出す：',
                        'alt': ['おかえり、初恋。第3話、告白したあと田口涼介と向き合う山根詩織']}},
        'en': {'topic': 'Like',
               'front': {'scene': 'On the festival night in high school, walking beside him, this is what she thought to herself:',
                         'tr': 'Even so, just being by your side was enough.',
                         'alt': ['Welcome Back, First Love Episode 3, high school flashback: on the festival night, Shiori Yamane walks beside Ryosuke Taguchi']},
               'back': {'scene': 'Ten years later, she gives the feeling a name and says it out loud:',
                        'tr': 'I like you, Taguchi.',
                        'alt': ['Welcome Back, First Love Episode 3: after her confession, Shiori Yamane faces Ryosuke Taguchi']}},
    },
}

ARTICLE = {'ja': 'https://knittinghiyori.com/welcome-back-first-love-ja/',
           'en': 'https://knittinghiyori.com/welcome-back-first-love-en/'}
CAL = {'ja': 'https://story.knittinghiyori.com/drama/calendar/ja/',
       'en': 'https://story.knittinghiyori.com/drama/calendar/en/'}
SPRING = {'ja': 'https://story.knittinghiyori.com/drama/the-early-spring/ja/',
          'en': 'https://story.knittinghiyori.com/drama/the-early-spring/en/'}

T = {
    'ja': {
        'html_lang': 'ja', 'og_locale': 'ja_JP', 'name': 'おかえり、初恋。',
        'title': 'おかえり、初恋。10年前と10年後｜第1〜3話の名場面とセリフ 回想めくりカード',
        'desc': 'ドラマ『おかえり、初恋。』では、高校時代と10年後の場面が何度も重なります。アイス、となりの席、ピアスの穴、また明日、つないだ手。第1〜3話の回想カードをめくって、10年前と10年後の同じ瞬間を見比べよう。場面写真とセリフ付き。',
        'og_title': 'おかえり、初恋。｜10年前と10年後 めくる回想カード',
        'og_desc': 'アイス、となりの席、ピアスの穴、もう一度抜け出す。カードをめくって、高校時代と10年後の同じ瞬間を。',
        'site': '・ストーリー', 'lang_label': '言語', 'crumb': 'ドラマ',
        'hero_alt': 'ドラマ『おかえり、初恋。』キービジュアル：街の光の中に立つ樋口幸平と林芽亜里、手書き風のタイトル',
        'h1': '10年たっても、<br><em>となり</em>に座る人がいる',
        'lede': 'ドラマ『おかえり、初恋。』では、高校時代いつもひとりだった2人が、10年後の同窓会で再会します。10年後に起きる出来事の多くは、高校時代のある一日への返事のよう。下の回想カードをめくって、同じ瞬間の10年前と10年後を見比べてみてください。',
        'status_h': '放送状況',
        'status': '第{a}話まで放送済み。第4話は10月29日（木）深夜放送',
        'status_aria': '全{t}話中{a}話放送済み',
        'btn_article': '放送スケジュール：全8話の放送日と最終回',
        'btn_cal': 'ドラマ配信スケジュール計算で予定に追加',
        'note': 'ネタバレあり：回想カードには第3話までのストーリーとセリフが出てきます。まだ見ていない方は、ブックマークしてあとでどうぞ。',
        'h2_cards': '10年前／10年後　めくる回想カード',
        'count': 'めくった思い出 <span id="wb-n">0</span>／<span id="wb-t">{n}</span> 組',
        'ep': '第{i}話', 'tag_front': '10年前・高校', 'tag_back': '10年後・現在',
        'flip_front': '10年後へめくる ↻', 'flip_back': '10年前に戻す ↻',
        'done': '全部の思い出をめくりました。10年前の言葉に、10年後の返事が届いています。',
        'done_btn': '各話のときめきシーンを見る（放送スケジュール記事）',
        'later': '1話放送されるごとに、回想カードを追加します。第4話（10月29日（木）深夜放送）のあと更新予定です。',
        'ad': '広告',
        'h2_people': '登場人物：はじまりの関係',
        'people': [('山根詩織', '林芽亜里', '25歳、内向的な会社員。高校時代はクラスでいつもひとりだった。'),
                   ('田口涼介', '樋口幸平', '25歳、エンジニア。高校時代は金髪にピアスの不良で、詩織の「ぼっち仲間」。'),
                   ('山根凪', '藤林泰也', '詩織の兄で美容師。ちょっと過保護。'),
                   ('柏木景', '高尾颯斗', '2人の高校の同級生。明るくて社交的。')],
        'actor_fmt': '{a}',
        'btn_map': '相関図をすべて見る（ネタバレなし）',
        'h2_manga': '原作漫画：詩織と田口の10年を先に読む',
        'manga': ['原作は、かめみずとらによる同名漫画。2021年にXで発表され、2026年10月時点で単行本は第7巻まで刊行、現在も連載中です。台湾では青文出版社から中国語版が出ています。',
                  '放送は週に30分。次の話までの待ち時間に、漫画を読むのもおすすめです。'],
        'disc': 'このページにはGoogle AdSenseの広告が表示されます。',
        'h2_faq': 'よくある質問',
        'faq': [('faq_episodes', '『おかえり、初恋。』は全何話？最終回はいつ？',
                 '全8話。MBSで毎週木曜深夜1:29から放送されています。途中で休止がなければ、第8話（最終回）は11月26日（木）深夜に放送されます。'),
                ('faq_timeline', '『おかえり、初恋。』の10年前と10年後は、何を描いている？',
                 '山根詩織と田口涼介は、高校時代クラスでいつもひとりだった2人。10年後、同窓会で再会します。物語は高校時代と現在の2つの時間を行き来し、10年後の場面の多くが高校時代の出来事に呼応しています。'),
                ('faq_manga', '『おかえり、初恋。』の原作は？',
                 'かめみずとらの同名漫画『おかえり、初恋。』が原作です。2021年にXで発表され、2026年10月時点で単行本は第7巻まで刊行、現在も連載中。台湾では青文出版社から中国語版が出ています。'),
                ('faq_update', '回想カードはいつ追加される？',
                 '1話放送されるごとに、10年前と10年後の回想カードを追加します。放送日と各話のサブタイトルは、放送スケジュールの記事で確認できます。')],
        'h2_more': '続けて読む',
        'more': [('wb_article_more', 'article', '『おかえり、初恋。』放送スケジュール', '全8話の放送日と最終回の日付'),
                 ('wb_calendar_more', 'cal', 'ドラマ配信スケジュール計算', '放送日をワンタップでGoogleカレンダーに追加'),
                 ('wb_more_the-early-spring', 'spring', '早春晴朗：原作解説', 'もうひとつの「10年」の物語'),
                 ('wb_more_hub', 'hub', 'ストーリー一覧（中国語）', 'ドラマ・小説・漫画のインタラクティブページ')],
        'src': '出典：MBS公式サイト、Real Sound、Wikipedia日本語版。セリフは各話から短く引用し、あらすじは当サイトによる要約です。場面写真：©2026 Welcome back, First love. Production committee, MBS。',
        'legal': '当サイトはアクセス解析（Google Analytics）と広告配信（Google AdSense）のためにCookieを使用し、一部にアフィリエイトリンクを含みます。',
        'privacy': 'プライバシーポリシー',
    },
    'en': {
        'html_lang': 'en', 'og_locale': 'en_US', 'name': 'Welcome Back, First Love',
        'title': 'Welcome Back, First Love: Then & Now | Episode 1–3 Scenes and Quotes as Flip Cards',
        'desc': 'In the Japanese drama Welcome Back, First Love (おかえり、初恋。), high school and ten years later keep echoing each other: an ice pop, sitting side by side, an ear piercing, see you tomorrow, holding hands. Flip the cards for Episodes 1–3 to compare the same moments, with stills, the original Japanese lines and English translations.',
        'og_title': 'Welcome Back, First Love | Then & Now flip cards',
        'og_desc': 'An ice pop, sitting side by side, an ear piercing, sneaking out again. Flip the cards to see the same moments in high school and ten years later.',
        'site': ' · Story', 'lang_label': 'Language', 'crumb': 'Dramas',
        'hero_alt': 'Key visual for the Japanese drama Welcome Back, First Love: Kohei Higuchi and Meari Hayashi against blurred city lights, with the handwritten title',
        'h1': 'Some people are still<br>sitting <em>next to you</em><br>ten years later',
        'lede': 'In the Japanese drama Welcome Back, First Love (おかえり、初恋。), two classmates who were always on their own in high school meet again at a reunion ten years later. So much of what happens now answers a day from back then. Flip the cards below to see the same moment, ten years apart.',
        'status_h': 'ON AIR',
        'status': 'Episodes 1–{a} have aired. Episode 4 airs late Thursday, Oct 29 (Japan time)',
        'status_aria': '{a} of {t} episodes aired',
        'btn_article': 'Episode guide: all 8 air dates and the finale',
        'btn_cal': 'Add the air dates to your calendar',
        'note': 'Spoilers ahead: the cards cover the story and lines up to Episode 3. Haven’t watched yet? Bookmark this page for later.',
        'h2_cards': 'Then / Now: flip the memory cards',
        'count': 'You’ve flipped <span id="wb-n">0</span> / <span id="wb-t">{n}</span> memories',
        'ep': 'Episode {i}', 'tag_front': 'THEN · HIGH SCHOOL', 'tag_back': 'NOW · TEN YEARS LATER',
        'flip_front': 'Flip to ten years later ↻', 'flip_back': 'Flip back to then ↻',
        'done': 'You’ve flipped every memory. Everything said ten years ago got its answer ten years later.',
        'done_btn': 'See each episode’s best moments (episode guide)',
        'later': 'New cards are added after each episode airs. Next update after Episode 4 (late Thursday, Oct 29, Japan time).',
        'ad': 'Advertisement',
        'h2_people': 'Who’s who at the start',
        'people': [('Shiori Yamane', 'Meari Hayashi', '25, a shy office worker. In high school she was always on her own in class.'),
                   ('Ryosuke Taguchi', 'Kohei Higuchi', '25, an engineer. In high school he was a blond delinquent with earrings, and Shiori’s fellow loner.'),
                   ('Nagi Yamane', 'Taiya Fujibayashi', 'Shiori’s older brother, a hairdresser. A little overprotective.'),
                   ('Kashiwagi (柏木景)', 'Hayato Takao', 'Their high school classmate. Cheerful and good with people.')],
        'actor_fmt': 'played by {a}',
        'btn_map': 'See the full character chart (spoiler-free)',
        'h2_manga': 'The original manga',
        'manga': ['The drama is based on the manga of the same name by Kamemizu Tora (かめみずとら). It first appeared on X in 2021; as of October 2026 the Japanese edition is up to volume 7, and it’s still ongoing. A Traditional Chinese edition is published in Taiwan by Ching Win Publishing (青文出版社).',
                  'With only 30 minutes a week, the manga is a nice way to fill the wait between episodes.'],
        'disc': 'This page shows Google AdSense ads.',
        'h2_faq': 'FAQ',
        'faq': [('faq_episodes', 'How many episodes does Welcome Back, First Love have, and when is the finale?',
                 'It has 8 episodes. It airs on MBS in Japan every Thursday at 1:29 a.m. late night (technically early Friday, Japan time). If there are no breaks, the finale, Episode 8, airs late Thursday, November 26.'),
                ('faq_timeline', 'What do the “ten years ago” and “ten years later” parts of Welcome Back, First Love show?',
                 'Shiori Yamane and Ryosuke Taguchi were the two kids in their high school class who were always on their own. Ten years later, they meet again at a class reunion. The story moves back and forth between high school and now, and many present-day scenes echo something that happened back then.'),
                ('faq_manga', 'What is Welcome Back, First Love based on?',
                 'It is based on the manga of the same name by Kamemizu Tora (おかえり、初恋。). It first appeared on X in 2021; as of October 2026 the Japanese edition is up to volume 7 and still ongoing. A Traditional Chinese edition is published in Taiwan by Ching Win Publishing.'),
                ('faq_update', 'When are new memory cards added?',
                 'New then-and-now cards are added after each episode airs. For air dates and episode titles, see the episode guide article.')],
        'h2_more': 'Keep reading',
        'more': [('wb_article_more', 'article', 'Welcome Back, First Love episode guide', 'All 8 air dates and the finale date'),
                 ('wb_calendar_more', 'cal', 'Drama Episode Schedule Calculator', 'Add release days to Google Calendar in one tap'),
                 ('wb_more_the-early-spring', 'spring', 'The Early Spring, explained', 'Another story about ten years'),
                 ('wb_more_hub', 'hub', 'All stories (in Chinese)', 'Interactive pages for dramas, novels and manga')],
        'src': 'Sources: MBS official site, Real Sound, Japanese Wikipedia. Lines are short quotes from each episode; English translations and story summaries are our own. Stills: ©2026 Welcome back, First love. Production committee, MBS.',
        'legal': 'This site uses cookies for analytics (Google Analytics) and ads (Google AdSense), and some links are affiliate links.',
        'privacy': 'Privacy',
    },
}

def esc(s):
    return html.escape(s, quote=True)

def card_face(lang, code, side, zh_face, tr):
    t, c = T[lang], tr[side]
    alts = c['alt']
    if len(alts) != len(zh_face['imgs']):
        sys.exit(f'{lang} {code} {side}：alt 有 {len(alts)} 個，中文版圖片有 {len(zh_face["imgs"])} 張')
    imgs = ''.join(f'<img class="wb-pic" src="{ASSET}{src}" width="960" height="540" loading="lazy" decoding="async" alt="{esc(a)}">'
                   for src, a in zip(zh_face['imgs'], alts))
    if len(alts) > 1:
        imgs = f'<div class="wb-pics">{imgs}</div>'
    small = f'<small lang="en">{esc(c["tr"])}</small>' if lang == 'en' else ''
    tag = t['tag_front'] if side == 'front' else t['tag_back']
    flip = t['flip_front'] if side == 'front' else t['flip_back']
    return f'''        <div class="wb-face wb-{side}">
          <span class="wb-tag">{tag}</span>
          <p class="wb-topic">{esc(tr['topic'])}</p>
          {imgs}
          <p class="wb-scene">{esc(c['scene'])}</p>
          <p class="wb-q" lang="ja"><span>{zh_face['quote']}</span>{small}</p>
          <button type="button" class="wb-flip" data-interact="flip_{code}">{flip}</button>
        </div>'''

def cards_html(lang):
    t, out, n = T[lang], [], 0
    if len(EPISODES[lang]) < len(ZH_EPS):
        sys.exit(f'{lang}：EPISODES 少了第 {len(EPISODES[lang]) + 1} 集的集名')
    for i, cards in enumerate(ZH_EPS):
        out.append(f'  <p class="wb-ep">{t["ep"].format(i=i + 1)}<small>{esc(EPISODES[lang][i])}</small></p>\n  <div class="wb-cards">')
        for code, faces in cards:
            if code not in CARDS or lang not in CARDS[code]:
                sys.exit(f'{lang}：CARDS 少了 {code} 這張卡的翻譯')
            tr = CARDS[code][lang]
            n += 1
            out.append(f'''    <article class="wb-card" data-card="{code}">
      <div class="wb-inner">
{card_face(lang, code, 'front', faces[0], tr)}
{card_face(lang, code, 'back', faces[1], tr)}
      </div>
    </article>
''')
        out.append('  </div>\n')
    return '\n'.join(out), n

def font_url(page):
    """Klee One 只載入用到的字（同中文版 &text= 子集）。"""
    parts = re.findall(r'<h1>(.*?)</h1>|<h2><span>(.*?)</span></h2>|<p class="wb-topic">(.*?)</p>|<p class="wb-q" lang="ja"><span>(.*?)</span>|<p class="big"[^>]*>(.*?)</p>|<b>(.*?)</b>', page, re.S)
    text = ''.join(''.join(p) for p in parts)
    text = html.unescape(re.sub(r'<[^>]+>', '', text))
    chars = ''.join(sorted(set(text) - set(' \n')))
    return 'https://fonts.googleapis.com/css2?family=Klee+One:wght@600&amp;display=swap&amp;text=' + quote(chars, safe='')

def build(lang):
    t = T[lang]
    url = BASE + lang + '/'
    links = {'article': ARTICLE[lang], 'cal': CAL[lang], 'spring': SPRING[lang], 'hub': 'https://story.knittinghiyori.com/'}
    cards, n = cards_html(lang)
    status = t['status'].format(a=STATUS['aired'], t=STATUS['total'])
    aria = t['status_aria'].format(a=STATUS['aired'], t=STATUS['total'])
    pct = round(STATUS['aired'] / STATUS['total'] * 100, 1)
    people = '\n'.join(f'    <li{" class=\"b\"" if i % 2 else ""}><b>{esc(nm)}</b><em>{esc(t["actor_fmt"].format(a=ac))}</em><br>{esc(d)}</li>'
                       for i, (nm, ac, d) in enumerate(t['people']))
    faq = '\n'.join(f'  <details><summary data-interact="{k}">{esc(q)}</summary><p>{esc(a)}</p></details>' for k, q, a in t['faq'])
    more = '\n'.join(f'    <li><a href="{links[dest]}" data-cta="{cid}"{"" if dest == "article" else " data-cta-type=\"story\""}>{esc(h)}<small>{esc(s)}</small></a></li>'
                     for cid, dest, h, s in t['more'])
    alt_names = [x for x in ['おかえり、初恋。', 'Welcome Back, First Love', '歡迎回來，初戀。'] if x != t['name']]
    ld_series = {'@context': 'https://schema.org', '@type': 'TVSeries', 'name': t['name'], 'alternateName': alt_names,
                 'inLanguage': 'ja', 'numberOfEpisodes': STATUS['total'], 'startDate': '2026-10-08', 'genre': ['Romance', 'Drama'],
                 'actor': [{'@type': 'Person', 'name': 'Kohei Higuchi' if lang == 'en' else '樋口幸平'},
                           {'@type': 'Person', 'name': 'Meari Hayashi' if lang == 'en' else '林芽亜里'}],
                 'author': {'@type': 'Person', 'name': 'Kamemizu Tora' if lang == 'en' else 'かめみずとら'},
                 'url': url, 'sameAs': ARTICLE[lang]}
    ld_crumb = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Story.', 'item': 'https://story.knittinghiyori.com/'},
        {'@type': 'ListItem', 'position': 2, 'name': t['name'], 'item': url}]}
    ld_faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for _, q, a in t['faq']]}
    def ld(o):
        return '<script type="application/ld+json">\n' + json.dumps(o, ensure_ascii=False, separators=(',', ':')) + '\n</script>'
    nav = '\n'.join(f'    <a href="{BASE}{p}" hreflang="{hl}" data-cta="lang_{c}"{" aria-current=\"page\"" if c == lang else ""}>{lbl}</a>'
                    for c, p, hl, lbl in [('zh', '', 'zh-Hant', '中文'), ('ja', 'ja/', 'ja', '日本語'), ('en', 'en/', 'en', 'English')])

    body = f'''<body>
<div class="wb-wrap">
<div class="kh-brand-row">
  <a class="kh-brand" href="https://story.knittinghiyori.com/" data-cta="brand_hub" data-cta-type="story"><img src="/icons/logo-knitting-120.webp" width="40" height="40" alt="">編織日和<span class="kh-site">{t['site']}</span></a>
  <nav class="wb-lang" aria-label="{t['lang_label']}">
{nav}
  </nav>
</div>
<p class="wb-crumb"><a href="https://story.knittinghiyori.com/" data-cta="crumb_hub" data-cta-type="story">Story.</a> › {t['crumb']}</p>

<main>
<section data-sec="intro" class="wb-bokeh">
  <figure class="wb-hero"><img src="{ASSET}welcome-back-first-love-key-visual-{lang}.webp" width="1200" height="632" alt="{esc(t['hero_alt'])}" fetchpriority="high"></figure>
  <h1>{t['h1']}</h1>
  <svg class="wb-line" viewBox="0 0 360 28" preserveAspectRatio="none" aria-hidden="true"><path d="M2 20 C 80 26, 150 8, 230 16 S 320 22, 336 12" fill="none" stroke="#e07c74" stroke-width="1.6" stroke-linecap="round"/><path d="M336 12 c-3-5-10-3-9 2 c1 4 9 8 9 8 s8-4 9-8 c1-5-6-7-9-2z" fill="none" stroke="#e07c74" stroke-width="1.4"/></svg>
  <p class="wb-lede">{esc(t['lede'])}</p>
  <div class="wb-status">
    <b>{t['status_h']}</b>
    <p>{esc(status)}</p>
    <div class="wb-bar" role="img" aria-label="{esc(aria)}"><i style="width:{pct}%"></i></div>
  </div>
  <div class="wb-btns">
    <a class="wb-btn" href="{ARTICLE[lang]}" data-cta="wb_article_top">{esc(t['btn_article'])}</a>
    <a class="wb-btn o" href="{CAL[lang]}" data-cta="wb_calendar_top" data-cta-type="story">{esc(t['btn_cal'])}</a>
  </div>
  <p class="wb-note">{esc(t['note'])}</p>
</section>

<section data-sec="cards">
  <h2><span>{esc(t['h2_cards'])}</span></h2>
  <div class="wb-count" aria-live="polite"><span class="wb-dots" aria-hidden="true"></span><span>{t['count'].format(n=n)}</span></div>

{cards}
  <div class="wb-done" id="wb-done" role="status">
    <p class="big" lang="ja">おかえり。</p>
    <p>{esc(t['done'])}</p>
    <a class="wb-btn c" href="{ARTICLE[lang]}" data-cta="wb_article_done">{esc(t['done_btn'])}</a>
  </div>
  <p class="wb-later">{esc(t['later'])}</p>
</section>

<div class="kh-ad kh-lift" aria-label="{t['ad']}">
  <span class="kh-ad__label">{t['ad']}</span>
  <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2022028565680247" data-ad-slot="2285424505" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>

<section data-sec="people">
  <h2><span>{esc(t['h2_people'])}</span></h2>
  <ul class="wb-ppl">
{people}
  </ul>
  <a class="wb-btn o" href="{ARTICLE[lang]}" data-cta="wb_article_map">{esc(t['btn_map'])}</a>
</section>

<section data-sec="manga">
  <h2><span>{esc(t['h2_manga'])}</span></h2>
  <div class="wb-manga">
{chr(10).join('    <p>' + esc(p) + '</p>' for p in t['manga'])}
    <p class="wb-disc">{esc(t['disc'])}</p>
  </div>
</section>

<div class="kh-ad kh-lift" aria-label="{t['ad']}">
  <span class="kh-ad__label">{t['ad']}</span>
  <ins class="adsbygoogle" style="display:block" data-ad-client="ca-pub-2022028565680247" data-ad-slot="2285424505" data-ad-format="auto" data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>

<section data-sec="faq" class="wb-faq">
  <h2><span>{esc(t['h2_faq'])}</span></h2>
{faq}
</section>

<section data-sec="more">
  <h2><span>{esc(t['h2_more'])}</span></h2>
  <ul class="wb-more">
{more}
  </ul>
  <p class="wb-src">{esc(t['src'])}</p>
</section>
</main>

<p class="kh-legal">{esc(t['legal'])}<a href="https://knittinghiyori.com/privacy-policy/">{t['privacy']}</a></p>
</div>
<footer>編織日和 · <a href="https://knittinghiyori.com/">knittinghiyori.com</a> · <a href="https://story.knittinghiyori.com/">Story.</a></footer>
{FLIP_JS}
</body>
</html>
'''
    head = f'''<!DOCTYPE html>
<html lang="{t['html_lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- Travelpayouts Drive（放在 head 最前面） -->
<script nowprocket data-noptimize="1" data-cfasync="false" data-wpfc-render="false" seraph-accel-crit="1" data-no-defer="1" data-cmp-ab="2">
  (function () {{
      var script = document.createElement("script");
      script.async = 1;
      script.setAttribute("data-cmp-ab","2");
      script.src = 'https://emrld.ltd/NTc4NjI0.js?t=578624';
      document.head.appendChild(script);
  }})();
</script>
<!-- Google AdSense（只有手動廣告：不帶 ?client=） -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" crossorigin="anonymous"></script>
<script>document.addEventListener('DOMContentLoaded',function(){{document.querySelectorAll('a[href]').forEach(function(a){{a.setAttribute('data-google-vignette','false')}})}});</script>
<meta name="spec-version" content="{SPEC}">
<!-- GA4（故事站標準追蹤） -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-ZQZHTYTRMQ"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{ dataLayer.push(arguments); }}
  gtag('js', new Date());
  gtag('config', 'G-ZQZHTYTRMQ', {{ cookie_domain: '.knittinghiyori.com' }});
</script>
<script>var HY_STORY_ID="welcome-back-first-love";var HY_PAGE_LANG="{lang}";document.documentElement.className+=" wb-js";</script>
<script src="/hy-story.js"></script>
<script>gtag("set",{{content_group:"story",work:"welcome-back-first-love",page_lang:"{lang}",page_title:"追劇|歡迎回來，初戀。|十年前後回憶翻面卡"}});</script>

<title>{esc(t['title'])}</title>
<meta name="description" content="{esc(t['desc'])}">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="zh-Hant" href="{BASE}">
<link rel="alternate" hreflang="ja" href="{BASE}ja/">
<link rel="alternate" hreflang="en" href="{BASE}en/">
<link rel="alternate" hreflang="x-default" href="{BASE}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(t['og_title'])}">
<meta property="og:description" content="{esc(t['og_desc'])}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{url}og.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{t['og_locale']}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/icons/favicon.ico?v=2" sizes="any">
<link rel="icon" href="/icons/favicon-32.png?v=2" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png?v=2">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="@@FONT@@">
{ld(ld_series)}
{ld(ld_crumb)}
{ld(ld_faq)}
{STYLE}
</head>
'''
    page = head + body
    page = page.replace('@@FONT@@', font_url(page))
    with open(os.path.join(WORK, lang, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'{lang}/index.html：{n} 張卡')

for lang in ('ja', 'en'):
    build(lang)
