"""Daily Five - a 5-question daily quiz with XP, levels, streaks, badges and a weekly leaderboard."""
import gradio as gr, sqlite3, hashlib, random, json
from datetime import datetime, timedelta, timezone

DB = "daily5.db"
IST = timezone(timedelta(hours=5, minutes=30))  # one "day" for everyone, India time
BADGES = {"first": ("🌱", "First Step"), "s3": ("🔥", "3-Day Streak"), "s7": ("🏆", "7-Day Streak"),
          "perfect": ("🎯", "Perfect 5"), "l3": ("⭐", "Level 3"), "l5": ("👑", "Level 5")}

# (question, options, correct index, tip) - short, simple English
BANK = [
 ("Someone asks for your OTP on a call. What do you do?", ["Share it", "Never share it", "Share half", "Send by SMS"], 1, "Never share your OTP. Real banks never ask for it."),
 ("Which password is strongest?", ["12345678", "myname", "T7#kq9!Lm", "password"], 2, "Mix letters, numbers and symbols."),
 ("A message says: 'You won ₹10 lakh! Click now.' It is most likely...", ["A scam", "A gift", "A bank note", "Safe"], 0, "Free-money messages are usually scams."),
 ("What does the lock 🔒 in a web address mean?", ["Site is fast", "Connection is private", "Site is free", "Site is new"], 1, "It means a private connection. Still check the site name."),
 ("You lose your phone. What first?", ["Wait a week", "Block SIM, lock accounts", "Buy a new one", "Post online"], 1, "Act fast: block the SIM and change passwords."),
 ("Who should know your UPI PIN?", ["Only you", "Family", "Shop owner", "Bank staff"], 0, "Keep your PIN secret. Always."),
 ("To RECEIVE money by UPI, you enter your PIN.", ["Yes, always", "No, never"], 1, "You enter PIN only to PAY, not to receive."),
 ("What is 10% of ₹500?", ["₹5", "₹50", "₹100", "₹10"], 1, "10% means divide by 10."),
 ("How can you save mobile data?", ["Use Wi-Fi when you can", "Stream in HD", "Keep all apps open", "Turn off phone"], 0, "Wi-Fi saves your data pack."),
 ("A torch app asks for all your contacts. You...", ["Allow", "Deny", "Pay", "Share"], 1, "Give only the permissions an app needs."),
 ("Where is it safe to get apps?", ["Unknown link", "Official app store", "WhatsApp forward", "SMS link"], 1, "Use the official app store only."),
 ("Why log out on a shared phone?", ["To save battery", "So others can't use your account", "To get points", "No reason"], 1, "Logging out protects your account."),
 ("You save ₹50 every day. How much in 10 days?", ["₹500", "₹50", "₹150", "₹5000"], 0, "50 x 10 = 500."),
 ("Two-step login (2FA) means...", ["Two same passwords", "A second check after password", "Two phones", "Two emails"], 1, "A second check stops most hackers."),
 ("A stranger sends a link to 'update KYC'. You...", ["Click it", "Call bank on its official number", "Send your ID", "Forward it"], 1, "Only use the bank's official number or app."),
 ("What drains battery faster?", ["Low brightness", "Full brightness", "Airplane mode", "Dark mode"], 1, "Lower brightness saves battery."),
 ("On public Wi-Fi, what is safest?", ["Bank login", "Read news only", "Enter card number", "Share OTP"], 1, "Avoid money apps on public Wi-Fi."),
 ("Which is a good money habit?", ["Spend everything", "Save a little each week", "Borrow often", "Hide bills"], 1, "Small savings grow over time."),
 ("A loan costs 3% per month. Over a year it is about...", ["3%", "12%", "36%", "0%"], 2, "3% x 12 months = 36%. Check the real cost."),
 ("Before sending money to someone new, you should...", ["Check the name shown", "Hurry", "Skip the check", "Share your PIN"], 0, "Always check the name before you pay."),
]

def today(): return datetime.now(IST).date()

def db():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

with db() as _c:
    _c.execute("create table if not exists users(name text primary key, pin text, xp int default 0, streak int default 0, best int default 0, last text, badges text default '[]')")
    _c.execute("create table if not exists plays(name text, day text, score int, xp int, primary key(name, day))")

def hpin(p): return hashlib.sha256(("d5" + p).encode()).hexdigest()

def daily_questions():
    rng = random.Random(today().isoformat())  # same 5 for everyone today
    return [dict(q=q, o=o, a=a, t=t) for q, o, a, t in rng.sample(BANK, 5)]

def played_today(name):
    with db() as c:
        return c.execute("select 1 from plays where name=? and day=?", (name, str(today()))).fetchone() is not None

def stats_html(name):
    with db() as c:
        u = c.execute("select * from users where name=?", (name,)).fetchone()
    lvl, into = u["xp"] // 100 + 1, u["xp"] % 100
    chips = "".join(f'<span class="chip" title="{BADGES[b][1]}">{BADGES[b][0]} {BADGES[b][1]}</span>' for b in json.loads(u["badges"])) or '<span class="chip">No badges yet</span>'
    status = "✅ Done today. Come back tomorrow!" if played_today(name) else "🎁 Today's challenge is ready!"
    return f"""<div class="card"><div class="hi">Hi {name} 👋</div>
<div class="big">Level {lvl}</div>
<div class="bar"><div style="width:{into}%"></div></div><div class="sm">{into}/100 XP to next level · {u['xp']} XP total</div>
<div class="row"><div><b>🔥 {u['streak']}</b><br><span class="sm">day streak</span></div><div><b>🏅 {u['best']}</b><br><span class="sm">best streak</span></div></div>
<div class="status">{status}</div></div><div class="chips">{chips}</div>"""

def lb_html(me=""):
    since = str(today() - timedelta(days=6))
    with db() as c:
        rows = c.execute("select name, sum(xp) s from plays where day>=? group by name order by s desc limit 10", (since,)).fetchall()
    if not rows: return '<div class="card2">No scores yet. Be the first! 🥇</div>'
    medals = ["🥇", "🥈", "🥉"]
    items = "".join(f'<div class="lbrow{" me" if r["name"] == me else ""}"><span>{medals[i] if i < 3 else i + 1}</span><span>{r["name"]}</span><b>{r["s"]} XP</b></div>' for i, r in enumerate(rows))
    return f'<div class="card2"><div class="sm">🏆 This week (last 7 days)</div>{items}</div>'

def view(w): return [gr.update(visible=w == k) for k in ("login", "home", "quiz", "result")]

def login(name, pin, st):
    name = (name or "").strip()[:16]
    if len(name) < 2 or not (pin or "").isdigit() or len(pin) != 4:
        return [st, "⚠️ Name: 2+ letters. PIN: 4 numbers.", "", ""] + view("login")
    with db() as c:
        u = c.execute("select pin from users where name=?", (name,)).fetchone()
        if u is None: c.execute("insert into users(name, pin) values(?,?)", (name, hpin(pin)))
        elif u["pin"] != hpin(pin): return [st, "❌ Wrong PIN for this name.", "", ""] + view("login")
    st = {"name": name}
    return [st, "", stats_html(name), lb_html(name)] + view("home")

def refresh(st): return stats_html(st["name"]), lb_html(st["name"])

def logout(): return [{}, ""] + view("login")

def show_q(st):
    i, q = st["i"], st["qs"][st["i"]]
    prog = f'<div class="sm">Question {i + 1} of 5</div><div class="bar"><div style="width:{(i + 1) * 20}%"></div></div>'
    return prog, f"### {q['q']}", gr.update(choices=q["o"], value=None, interactive=True), "", gr.update(visible=True), gr.update(visible=False)

def start(st):
    if played_today(st["name"]):
        return [st, "✅ You already played today. Come back tomorrow!", *view("home"), "", "", gr.update(), "", gr.update(), gr.update()]
    st.update(qs=daily_questions(), i=0, score=0)
    return [st, "", *view("quiz"), *show_q(st)]

def check(choice, st):
    if choice is None: return st, "👆 Please choose an answer.", gr.update(), gr.update(), gr.update()
    q = st["qs"][st["i"]]
    ok = choice == q["o"][q["a"]]
    st["score"] += ok
    fb = f'<div class="fb {"ok" if ok else "no"}">{"✅ Correct! +10 XP" if ok else "❌ Not quite. Answer: " + q["o"][q["a"]]}<br><span class="sm">💡 {q["t"]}</span></div>'
    return st, fb, gr.update(visible=False), gr.update(visible=True, value="See my result ➜" if st["i"] == 4 else "Next ➜"), gr.update(interactive=False)

def finish(st):
    name, score, t = st["name"], st["score"], today()
    with db() as c:
        if c.execute("select 1 from plays where name=? and day=?", (name, str(t))).fetchone(): return "<div class='card'>Already saved.</div>"
        u = c.execute("select * from users where name=?", (name,)).fetchone()
        streak = u["streak"] + 1 if u["last"] == str(t - timedelta(days=1)) else 1
        gain = score * 10 + (20 if score == 5 else 0) + min(streak, 7) * 5
        xp = u["xp"] + gain; lvl = xp // 100 + 1
        have = set(json.loads(u["badges"]))
        earned = {"first"} | ({"s3"} if streak >= 3 else set()) | ({"s7"} if streak >= 7 else set()) | ({"perfect"} if score == 5 else set()) | ({"l3"} if lvl >= 3 else set()) | ({"l5"} if lvl >= 5 else set())
        new = earned - have
        c.execute("insert into plays values(?,?,?,?)", (name, str(t), score, gain))
        c.execute("update users set xp=?, streak=?, best=?, last=?, badges=? where name=?", (xp, streak, max(streak, u["best"]), str(t), json.dumps(sorted(have | earned)), name))
    newb = "".join(f'<div class="chip pop">{BADGES[b][0]} New badge: {BADGES[b][1]}</div>' for b in new)
    msg = "🎉 Perfect!" if score == 5 else "👏 Good job!" if score >= 3 else "💪 Keep going!"
    return f'<div class="card"><div class="big">{msg}</div><div class="big">{score}/5</div><div class="gain">+{gain} XP</div><div class="sm">{score*10} quiz · {20 if score==5 else 0} perfect bonus · {min(streak,7)*5} streak bonus</div><div class="sm">🔥 {streak}-day streak</div></div>{newb}'

def nxt(st):
    st["i"] += 1
    if st["i"] >= 5:
        r = finish(st); name = st["name"]
        return [st, *view("result"), "", "", gr.update(), "", gr.update(), gr.update(), r, stats_html(name), lb_html(name)]
    return [st, *view("quiz"), *show_q(st), gr.update(), gr.update(), gr.update()]

CSS = """
.gradio-container{max-width:480px!important;margin:auto!important;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif!important}
.card{background:linear-gradient(135deg,#6d28d9,#db2777);color:#fff;border-radius:22px;padding:20px;text-align:center;box-shadow:0 8px 24px #6d28d955}
.card2{background:var(--block-background-fill);border:1px solid var(--border-color-primary);border-radius:18px;padding:14px}
.hi{font-size:18px}.big{font-size:32px;font-weight:800;margin:4px 0}.sm{font-size:13px;opacity:.85}.gain{font-size:28px;font-weight:800;color:#fde68a}
.bar{background:#ffffff40;border-radius:99px;height:12px;margin:8px 0;overflow:hidden}.bar div{background:#fde68a;height:100%;border-radius:99px;transition:width .4s}
.row{display:flex;justify-content:space-around;margin:12px 0;font-size:20px}.status{background:#00000030;border-radius:12px;padding:8px;margin-top:8px;font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}.chip{background:#ede9fe;color:#4c1d95;border-radius:99px;padding:6px 12px;font-size:14px;font-weight:600}
.pop{margin-top:10px;text-align:center;font-size:17px;animation:pop .5s}@keyframes pop{from{transform:scale(.5);opacity:0}to{transform:scale(1);opacity:1}}
.lbrow{display:flex;justify-content:space-between;gap:10px;padding:10px 6px;border-bottom:1px solid #8883;font-size:17px}.lbrow span:nth-child(2){flex:1}.me{background:#fde68a55;border-radius:10px;font-weight:700}
.fb{border-radius:14px;padding:12px;font-size:17px}.ok{background:#dcfce7;color:#14532d}.no{background:#fee2e2;color:#7f1d1d}
button{min-height:52px!important;font-size:18px!important;border-radius:14px!important}
label span{font-size:17px!important}.gr-radio label,fieldset label{padding:12px!important}
footer{display:none!important}
"""

import inspect
_style = dict(css=CSS, theme=gr.themes.Soft(primary_hue="violet"))
# Gradio 6 moved css/theme from Blocks() to launch(); support both old and new versions
_new = "css" not in inspect.signature(gr.Blocks.__init__).parameters
BK = {} if _new else _style
LK = dict(_style) if _new else {}
if "ssr_mode" in inspect.signature(gr.Blocks.launch).parameters: LK["ssr_mode"] = False

with gr.Blocks(title="Daily Five", **BK) as demo:
    st = gr.State({})
    gr.Markdown("# 🖐️ Daily Five\n5 quick questions. Earn XP. Keep your streak!")
    with gr.Column(visible=True) as login_col:
        name = gr.Textbox(label="Your name", max_lines=1, max_length=16)
        pin = gr.Textbox(label="4-number PIN (remember it)", type="password", max_length=4)
        lmsg = gr.Markdown()
        lbtn = gr.Button("Start ➜", variant="primary")
    with gr.Column(visible=False) as home_col:
        stats = gr.HTML(); hmsg = gr.Markdown()
        play = gr.Button("▶️ Play today's 5", variant="primary")
        lb = gr.HTML()
        with gr.Row():
            rbtn = gr.Button("🔄 Refresh"); obtn = gr.Button("Log out")
    with gr.Column(visible=False) as quiz_col:
        prog = gr.HTML(); qtext = gr.Markdown()
        radio = gr.Radio(choices=[], label="Choose one", interactive=True)
        fb = gr.HTML()
        cbtn = gr.Button("Check ✔️", variant="primary"); nbtn = gr.Button("Next ➜", visible=False, variant="primary")
    with gr.Column(visible=False) as res_col:
        res = gr.HTML()
        hbtn = gr.Button("🏠 Home", variant="primary")

    V = [login_col, home_col, quiz_col, res_col]
    lbtn.click(login, [name, pin, st], [st, lmsg, stats, lb] + V)
    rbtn.click(refresh, st, [stats, lb])
    obtn.click(logout, None, [st, lmsg] + V)
    Q = [prog, qtext, radio, fb, cbtn, nbtn]
    play.click(start, st, [st, hmsg] + V + Q)
    cbtn.click(check, [radio, st], [st, fb, cbtn, nbtn, radio])
    nbtn.click(nxt, st, [st] + V + Q + [res, stats, lb])
    hbtn.click(lambda: view("home"), None, V)

if __name__ == "__main__":
    demo.queue().launch(**LK)
