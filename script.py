#!/usr/bin/env python3
import os
import subprocess
import json
import socket
from datetime import datetime
from tqdm import tqdm

# ---------------- VISUAL STYLES ----------------

class Colors:
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    RESET   = '\033[0m'
    BOLD    = '\033[1m'

def banner():
    os.system('clear')
    print(f"""{Colors.CYAN}
    ███████╗███████╗ ██████╗ ██████╗ ██████╗ ███████╗
    ██╔════╝██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔════╝
    ███████╗█████╗  ██║     ██║   ██║██████╔╝███████╗
    ╚════██║██╔══╝  ██║     ██║   ██║██╔═══╝ ╚════██║
    ███████║███████╗╚██████╗╚██████╔╝██║     ███████║
    ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝     ╚══════╝
    {Colors.WHITE}>> Advanced Recon Automation Toolkit <<
    {Colors.RESET}""")

def print_success(msg):
    print(f"{Colors.GREEN}[✓] {msg}{Colors.RESET}")

def print_error(msg):
    print(f"{Colors.RED}[✖] {msg}{Colors.RESET}")

def print_info(msg):
    print(f"{Colors.BLUE}[ℹ] {msg}{Colors.RESET}")

def print_warn(msg):
    print(f"{Colors.YELLOW}[!] {msg}{Colors.RESET}")

# ---------------- CONFIG SYSTEM ----------------

CONFIG_FILE = "config.json"

tools = {
    "subfinder": "sudo apt install subfinder -y",
    "httpx-toolkit": "sudo apt install httpx-toolkit -y",
    "dirb": "sudo apt install dirb -y",
    "go": "sudo apt install golang-go -y",
    "whatweb": "sudo apt install whatweb -y",
    "wafw00f": "sudo apt install wafw00f -y",
}

def load_all():
    return json.load(open(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else {}

def save_all(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

def clear_targets():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print_success("Hedefler başarıyla silindi.")
    else:
        print_warn("Silinecek yapılandırma dosyası bulunamadı.")
    input(f"\n{Colors.CYAN}Devam etmek için Enter'a bas...{Colors.RESET}")

# ---------------- TARGET HANDLING ----------------

def new_target():
    print(f"\n{Colors.YELLOW}>> Yeni Hedef Tanımlama{Colors.RESET}")
    t = input(f"{Colors.BOLD}Hedef Domain (örn: site.com): {Colors.RESET}").strip().replace("https://", "").replace("http://", "").rstrip("/")
    cfg = load_all()
    cfg[t] = cfg.get(t, {})
    save_all(cfg)
    return t

def select_target():
    banner()
    cfg = load_all()
    if not cfg:
        return new_target()

    print(f"{Colors.CYAN}╔════════════════════════════════╗")
    print(f"║        HEDEF LİSTESİ           ║")
    print(f"╚════════════════════════════════╝{Colors.RESET}")
    
    keys = list(cfg.keys())
    for i, d in enumerate(keys, 1):
        print(f"{Colors.GREEN}{i}){Colors.RESET} {d}")
    print(f"{Colors.YELLOW}0){Colors.RESET} Yeni hedef ekle")

    sec = input(f"\n{Colors.CYAN}Seçiminiz: {Colors.RESET}")
    if sec.isdigit():
        sec = int(sec)

        if sec == 0:
            return new_target()
        if 1 <= sec <= len(keys):
            return keys[sec - 1]

    print_error("Geçersiz seçim -> Yeni hedef oluşturuluyor.")
    return new_target()

# ---------------- UTILS ----------------

def fix_url(u):
    u = u.strip().replace("https://https://", "").replace("http://http://", "")
    return u if u.startswith("http") else "https://" + u

def host_resolves(host):
    try:
        socket.gethostbyname(host)
        return True
    except:
        return False

def url_is_alive(url, timeout=10):
    try:
        ret = subprocess.run(["curl", "-sI", "--max-time", str(timeout), url], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return "HTTP/" in ret.stdout + ret.stderr
    except:
        return False

# ---------------- TOOL CHECK ----------------

def check_tools():
    print(f"\n{Colors.CYAN}[*] Sistem Bağımlılıkları Kontrol Ediliyor...{Colors.RESET}")
    for tool, cmd in tools.items():
        if subprocess.call(f"command -v {tool} >/dev/null", shell=True) != 0:
            print_warn(f"{tool} eksik -> Kurulum başlatılıyor...")
            subprocess.run(cmd, shell=True)
        else:
            print_success(f"{tool} tespit edildi.")

    if subprocess.call("command -v gau >/dev/null", shell=True) != 0:
        print_warn("gau eksik -> Go ile kuruluyor...")
        os.system("go install github.com/lc/gau/v2/cmd/gau@latest")
        os.system("sudo cp ~/go/bin/gau /usr/local/bin/")
    else:
        print_success("gau tespit edildi.")

# ---------------- FEATURES ----------------

def manual_sub_add(target):
    print(f"\n{Colors.BLUE}>> Manuel Subdomain Ekleme{Colors.RESET}")
    cfg = load_all()
    subs = cfg[target].get("subdomains", [])

    ekle = input(f"{Colors.BOLD}Subdomain girin (örn: api.site.com): {Colors.RESET}").strip()
    if not ekle:
        print_warn("Giriş boş bırakılamaz.")
        return

    if not ekle.startswith("http"):
        ekle = "https://" + ekle

    if ekle not in subs:
        subs.append(ekle)
        cfg[target]["subdomains"] = subs
        save_all(cfg)
        print_success(f"Eklendi: {ekle}")
    else:
        print_warn("Bu subdomain zaten listede mevcut.")
    
    input(f"\n{Colors.CYAN}Devam etmek için Enter...{Colors.RESET}")

def subdomain_scan(target):
    print_info(f"Subdomain taraması başlatılıyor: {Colors.BOLD}{target}{Colors.RESET}")
    cmd = f"subfinder -silent -d {target} | httpx-toolkit -silent -threads 200"
    result = subprocess.getoutput(cmd)

    if not result.strip():
        print_error("Hiçbir subdomain bulunamadı.")
        input("Devam etmek için Enter...")
        return []

    domains = [d.strip() for d in result.splitlines()]
    print(f"\n{Colors.GREEN}📌 Aktif Subdomainler:{Colors.RESET}")
    for i, d in enumerate(domains, 1):
        print(f"{Colors.CYAN}{i}){Colors.RESET} {d}")

    cfg = load_all()
    cfg[target] = {"subdomains": domains, "last_scan": str(datetime.now())}
    save_all(cfg)

    input(f"\n{Colors.CYAN}Devam etmek için Enter...{Colors.RESET}")
    return domains

def dirb_scan(target):
    cfg = load_all()
    subs = cfg[target].get("subdomains", [])
    if not subs:
        print_error("Kayıtlı subdomain yok. Önce tarama yapınız.")
        input("Devam..."); return

    print(f"\n{Colors.YELLOW}>> Hedef Seçimi (Dirb):{Colors.RESET}")
    for i, s in enumerate(subs, 1): print(f"{Colors.CYAN}{i}){Colors.RESET} {s}")

    sec = input("Seçim: ")
    if not sec.isdigit(): return
    url = subs[int(sec)-1]
    host = url.replace("https://","").replace("http://","")

    if not host_resolves(host): print_error("DNS çözümlenemedi."); return
    if not url_is_alive(url): print_error("Hedef erişilebilir değil (Down)."); return

    print_info(f"DIRB Başlatılıyor → {url}")
    wl = "/usr/share/wordlists/dirb/common.txt"
    out = f"results/{host}_dirb.txt"
    os.makedirs("results", exist_ok=True)
    os.system(f"dirb {url} {wl} -o {out}")
    print_success(f"Tarama tamamlandı. Kayıt: {out}")
    input("Devam...")

def js_scan(target):
    if not os.path.exists(os.path.expanduser("~/tools/LinkFinder")):
        print_warn("LinkFinder bulunamadı, kuruluyor...")
        os.system("git clone https://github.com/GerbenJavado/LinkFinder.git ~/tools/LinkFinder")
        os.system("pip install -r ~/tools/LinkFinder/requirements.txt --break-system-packages")

    print(f"\n{Colors.CYAN}1){Colors.RESET} Listeden Seç\n{Colors.CYAN}2){Colors.RESET} Manuel URL Gir")
    mode = input("Mod Seçimi: ")

    if mode == "2":
        js = input("JS URL: ").strip()
        os.system(f"python3 ~/tools/LinkFinder/linkfinder.py -i {js} -o cli")
        input("Devam..."); return

    subs = load_all()[target].get("subdomains", [])
    for i, s in enumerate(subs, 1): print(f"{Colors.CYAN}{i}){Colors.RESET} {s}")

    sec = input("Seçim: ")
    url = subs[int(sec)-1]
    os.system(f"python3 ~/tools/LinkFinder/linkfinder.py -i {url} -o cli")
    input("Devam...")

def gau_scan(target):
    subs = load_all()[target].get("subdomains", [])
    for i, s in enumerate(subs, 1): print(f"{Colors.CYAN}{i}){Colors.RESET} {s}")

    sec = input("Seçim: ")
    print_info("GAU (Get All Urls) çalıştırılıyor...")
    os.system(f"gau {subs[int(sec)-1]}")
    input("Devam...")

def cms_detect(target):
    print_info(f"CMS Tespiti yapılıyor: {target}")
    os.system(f"whatweb -a 3 {fix_url(target)}")
    input("Devam...")

def waf_detect(target):
    print_info(f"WAF Tespiti yapılıyor: {target}")
    os.system(f"wafw00f {fix_url(target)}")
    input("Devam...")

def full_auto(target):
    print(f"\n{Colors.RED}🚀 FULL OTO SALDIRI MODU BAŞLATILDI{Colors.RESET}")
    cfg = load_all()
    subs = cfg[target].get("subdomains") or subdomain_scan(target)

    for d in tqdm(subs, desc=f"{Colors.GREEN}İşleniyor{Colors.RESET}", unit="sub"):
        safe = d.replace("https://","").replace("http://","")
        os.system(f"dirb {d} /usr/share/wordlists/dirb/common.txt > results/{safe}_dirb.txt")
        os.system(f"python3 ~/tools/LinkFinder/linkfinder.py -i {d} > results/{safe}_js.txt")
        os.system(f"gau {d} > results/{safe}_gau.txt")

    print_success("Tüm otomatik taramalar tamamlandı.")
    input("Devam...")

# ---------------- MAIN MENU ----------------

def start_menu():
    banner()
    print(f"""
{Colors.CYAN}┌────────────────────────────────────────┐
│             ANA KONTROL                │
└────────────────────────────────────────┘{Colors.RESET}
{Colors.GREEN}1){Colors.RESET} Hedef Seç / Değiştir
{Colors.RED}2){Colors.RESET} Hedef Veritabanını Temizle
{Colors.YELLOW}0){Colors.RESET} Çıkış
""")
    s = input(f"{Colors.BOLD}Seçiminiz > {Colors.RESET}")

    if s == "1": return select_target()
    if s == "2": clear_targets()
    if s == "0": exit()

def menu():
    target = start_menu()
    while True:
        if not target: # Hedef silinirse veya boşsa başa dön
            target = start_menu()
            continue
            
        banner()
        print(f"""
{Colors.YELLOW}⚡ AKTİF HEDEF:{Colors.RESET} {Colors.BOLD}{Colors.RED}{target}{Colors.RESET}

{Colors.CYAN}╔════ RECONNAISSANCE ════════════════════════════╗
║ {Colors.GREEN}1){Colors.RESET} Subdomain Scan  {Colors.GREEN}2){Colors.RESET} Dirb Scan       ║
║ {Colors.GREEN}3){Colors.RESET} JS Scan         {Colors.GREEN}4){Colors.RESET} GAU Scan        ║
╠════ ANALYSIS ══════════════════════════════════╣
║ {Colors.GREEN}5){Colors.RESET} CMS Tespit      {Colors.GREEN}6){Colors.RESET} WAF Tespit      ║
╠════ AUTOMATION & UTILS ════════════════════════╣
║ {Colors.GREEN}8){Colors.RESET} Manuel Subdomain                                                ║      
║ {Colors.GREEN}9){Colors.RESET} Hedef Değiştir  {Colors.YELLOW}0){Colors.RESET} Çıkış           ║
╚════════════════════════════════════════════════╝
""")

        sec = input(f"{Colors.BOLD}Komut > {Colors.RESET}").strip()

        if sec == "1": subdomain_scan(target)
        elif sec == "2": dirb_scan(target)
        elif sec == "3": js_scan(target)
        elif sec == "4": gau_scan(target)
        elif sec == "5": cms_detect(target)
        elif sec == "6": waf_detect(target)
        elif sec == "8": manual_sub_add(target)
        elif sec == "9": target = start_menu()
        elif sec == "0": 
            print(f"\n{Colors.RED}Sistem kapatılıyor. Güvenli günler.{Colors.RESET}")
            exit()
        else: 
            print_error("Geçersiz komut.")
            input("Devam...")

if __name__ == "__main__":
    banner()
    check_tools()
    input(f"\n{Colors.GREEN}Araçlar hazır. Başlamak için Enter...{Colors.RESET}")
    menu()
