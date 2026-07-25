# Prevádzkový návod VORU (runbook)

Praktické postupy pre bežnú správu servera. Server: `ssh root@195.201.147.90`,
kód v `/root/TMB`, konfigurácia v `/root/TMB/.env.master` (načíta ju systemd
služba `platby-web`). Po každej zmene `.env.master` treba
`systemctl restart platby-web`.

---

## 0. Bezpečná úprava .env.master (odporúčaný spôsob)

Aby sa nano nerozbilo a secret sa nedostal do histórie príkazov, používaj tento
pomocník — hodnotu vloží skryto a nahradí presne jeden riadok:

```bash
setkey() {
  local key="$1" f=/root/TMB/.env.master
  printf "Vlož hodnotu pre %s (nezobrazí sa): " "$key"
  read -rs val; echo
  [ -z "$val" ] && { echo "prázdne — zrušené"; return 1; }
  cp "$f" "$f.bak.$(date +%s)"
  grep -v "^$key=" "$f.bak."* 2>/dev/null >/dev/null
  grep -v "^$key=" "$f" > "$f.tmp" && printf '%s=%s\n' "$key" "$val" >> "$f.tmp" && mv "$f.tmp" "$f"
  echo "$key nastavený (záloha $f.bak.*)"
}
```

Vlož raz do terminálu (definuje funkciu na aktuálnu reláciu). Potom napr.:

```bash
setkey ANTHROPIC_API_KEY      # vypýta hodnotu skryto
systemctl restart platby-web  # aplikuje zmenu
```

Kontrola, že kľúč existuje práve raz (bez zobrazenia hodnoty):

```bash
grep -c '^ANTHROPIC_API_KEY=' /root/TMB/.env.master   # musí byť 1
```

---

## 1. Rotácia kľúčov

Pravidlo: **`WEBAPP_SECRET` NIKDY nerotovať** — šifruje heslá schránok klientov,
rotácia by ich znefunkčnila. Ostatné nižšie sa rotovať dajú bezpečne.

Univerzálny postup: 1) vytvor nový secret u poskytovateľa, 2) `setkey <KĽÚČ>`,
3) `systemctl restart platby-web`, 4) over funkčnosť, 5) až potom zmaž starý
secret u poskytovateľa.

### 1a. Anthropic API key (`ANTHROPIC_API_KEY`)
- **Kde:** console.anthropic.com → Settings → **API Keys**
- **Create Key** → skopíruj nový (`sk-ant-...`)
- Server: `setkey ANTHROPIC_API_KEY` → vlož → `systemctl restart platby-web`
- Over: `cd /root/TMB && .venv/bin/python -m bill_agent run-all fetch` (log v
  `agent.log` nesmie hlásiť auth chybu), alebo počkaj na ranný beh
- Nakoniec v konzole **Delete** starý kľúč
- Dopad: žiadny na dáta; medzi zmenou a reštartom by AI spracovanie zlyhalo

### 1b. Google client secret (`GOOGLE_CLIENT_SECRET`)
- **Kde:** console.cloud.google.com → projekt VORU → **APIs & Services →
  Credentials** → OAuth 2.0 Client (Web)
- **Add Secret** (Google umožní mať 2 naraz) → skopíruj nový
- Server: `setkey GOOGLE_CLIENT_SECRET` → `systemctl restart platby-web`
- Over: skús pripojiť Gmail cez `/mailboxes` (tlačidlo „Pripojiť Gmail")
- **Client ID sa nemení** → existujúce Gmail pripojenia klientov fungujú ďalej
- Po overení **Disable/Delete** starý secret
- Dopad: pridaním nového secretu (nie zmazaním starého skôr) nula výpadku

### 1c. Turnstile secret (`TURNSTILE_SECRET`)
- **Kde:** dash.cloudflare.com → **Turnstile** → widget voru.sk → **Settings →
  Rotate Secret Key**
- Skopíruj nový **Secret Key** (Site Key sa nemení, je verejný)
- Server: `setkey TURNSTILE_SECRET` → `systemctl restart platby-web`
- Over: otvor `/register` a dokonči registráciu (widget musí prejsť)
- Dopad: medzi rotáciou a reštartom by registrácie zlyhali — rob rýchlo

### 1d. SMTP heslo (`SMTP_PASSWORD`)
- Je to heslo schránky **agent@voru.sk** (SMTP_USER).
- **Kde:** webmail/administrácia Webhouse → schránka agent@voru.sk → **zmena
  hesla** → nastav nové
- Server: `setkey SMTP_PASSWORD` → `systemctl restart platby-web`
- Over: `/admin` → Zdravie systému → **Poslať testovací e-mail** (musí prísť)
- Dopad: medzi zmenou a reštartom by odchádzajúce e-maily zlyhali — rob rýchlo

### 1e. Stripe webhook secret (`STRIPE_WEBHOOK_SECRET`)
- **Kde:** dashboard.stripe.com/webhooks → endpoint **elegant-spark** → **Roll
  secret** (expirácia: Immediately) → cez ikonu oka skopíruj nový `whsec_...`
- Server: `setkey STRIPE_WEBHOOK_SECRET` → `systemctl restart platby-web`
- Over: v Stripe pri endpointe **Send test webhook** → v `agent.log`/aplikácii
  nesmie byť „signature verification failed"
- Dopad: Stripe zlyhané doručenia opakuje, takže krátky výpadok je bez straty

---

## 2. Zálohy mimo server (Hetzner Storage Box)

`scripts/backup.sh` denne balí `clients/`, `webapp.db` a `.env.master` do
`/root/backups` (14 dní). Keby server zlyhal, zlyhajú aj zálohy — treba ich
kopírovať mimo.

### 2a. Objednaj Storage Box
- Hetzner konzola (robot.hetzner.com alebo console.hetzner.cloud) → **Storage
  Box** → najmenší **BX11** (1 TB, ~3,20 €/mes.) stačí
- V nastaveniach boxu zapni **SSH support** (a voliteľne „External
  reachability"). Poznač si používateľa `uXXXXXX` a hostname
  `uXXXXXX.your-storagebox.de`

### 2b. Nastav prihlásenie kľúčom (bez hesla)
Na serveri:
```bash
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N ""   # ak ešte nemáš kľúč
# nahraj verejný kľúč na Storage Box (port 23!):
cat /root/.ssh/id_ed25519.pub | ssh -p 23 uXXXXXX@uXXXXXX.your-storagebox.de install-ssh-key
```
(Storage Box používa **port 23** pre SSH/rsync, nie 22.) Otestuj:
```bash
ssh -p 23 uXXXXXX@uXXXXXX.your-storagebox.de ls
```

### 2c. Automatický sync po zálohe
Pridaj do cronu (`crontab -e`) riadok, ktorý beží hodinu po zálohe (4:15):
```
15 4 * * *  rsync -a --delete -e "ssh -p 23" /root/backups/ uXXXXXX@uXXXXXX.your-storagebox.de:voru/ >> /root/TMB/agent.log 2>&1
```
Ručné overenie hneď teraz:
```bash
rsync -a --delete -e "ssh -p 23" /root/backups/ uXXXXXX@uXXXXXX.your-storagebox.de:voru/
ssh -p 23 uXXXXXX@uXXXXXX.your-storagebox.de ls -la voru/
```
Zálohy obsahujú `.env.master` (tajomstvá) — Storage Box drž len pre seba,
nezdieľaj prístup.

---

## 3. DKIM u Webhouse

SPF a DMARC už máš nastavené a platné. DKIM podpisuje odchádzajúcu poštu
privátnym kľúčom na strane mailservera (Webhouse), ty do DNS pridáš verejný
kľúč. Preto to musí zapnúť Webhouse.

### Postup
1. Napíš podpore Webhouse (support@webhouse.sk) — vzor:
   > Dobrý deň, prosím o zapnutie DKIM podpisovania pre odchádzajúcu poštu
   > domény **voru.sk** (schránka agent@voru.sk). Pošlite mi prosím DKIM DNS
   > záznam (selektor a hodnotu TXT), ktorý mám pridať do DNS zóny. Ďakujem.
2. Webhouse ti vráti záznam typu:
   `selektor._domainkey.voru.sk  TXT  "v=DKIM1; k=rsa; p=<dlhý_kľúč>"`
3. Pridaj ho v DNS zóne (Webhouse DNS správa) — **pozor na rozdeľovanie
   dlhej hodnoty** (formulár Webhouse delí TXT na medzerách; ak treba, vlož
   celú hodnotu do úvodzoviek ako pri SPF/DMARC).
4. Over po pár hodinách:
   ```bash
   dig +short TXT selektor._domainkey.voru.sk
   ```
   (nahraď „selektor" tým, čo dá Webhouse)
5. Pošli si testovací e-mail cez `/admin` → mal by prejsť DKIM. Celkovú
   doručiteľnosť si overíš poslaním na **check-auth@verifier.port25.com**
   (vráti report SPF/DKIM/DMARC = pass) alebo cez mail-tester.com.

Rovnaký postup zopakuj pre .cz/.pl/.at/.hu, ak z nich posielaš poštu.

---

## 4. UptimeRobot (monitoring dostupnosti)

Zadarmo ťa upozorní e-mailom/SMS, keď web spadne.
1. Registrácia na **uptimerobot.com** (free plán stačí)
2. **+ Add New Monitor**
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `VORU`
   - URL: `https://voru.sk/healthz`
   - Monitoring interval: **5 minút**
   - (voliteľné) **Keyword monitoring** → keyword `ok` → upozorní aj keď web
     odpovie, ale healthz nevráti `ok`
3. **Alert Contacts** → pridaj svoj e-mail (a prípadne telefón)
4. Ulož. Zelený stav = beží; pri výpadku ti príde upozornenie.

Voliteľne pridaj druhý monitor na `https://voru.cz/healthz` atď.

---

## Rýchle overenie stavu servera

```bash
systemctl is-active platby-web        # active
curl -s https://voru.sk/healthz       # ok
tail -n 30 /root/TMB/agent.log        # posledná aktivita cronu/enginu
```
Alebo všetko naraz v aplikácii: `/admin` → **Zdravie systému**.
