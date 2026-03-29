#!/usr/bin/env python3
“””
GeoIntel KB — Edge Function Builder
Dato un URL di sito, genera automaticamente la Edge Function Supabase.
“””

import sys
import re
import json
import requests

# ── CONFIG — modifica questi valori ──────────────────────────────────────────

ANTHROPIC_API_KEY = “sk-ant-INSERISCI-LA-TUA-KEY-QUI”
SUPABASE_URL = “https://chuvfdbpwiszjuoyhvlw.supabase.co”
SUPABASE_KEY = “eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNodXZmZGJwd2lzemp1b3lodmx3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQzOTU2NzcsImV4cCI6MjA4OTk3MTY3N30.7OAuk36xTNa6cFyF2cnpBRUtgeZpttAyi-ZA28_fhdU”

# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {“User-Agent”: “Mozilla/5.0 GeoIntelKB/1.0”}

def fetch_sitemap_index(site_url):
“”“Trova la sitemap del sito.”””
candidates = [
site_url.rstrip(”/”) + “/sitemap.xml”,
site_url.rstrip(”/”) + “/sitemap_index.xml”,
]
for url in candidates:
try:
r = requests.get(url, headers=HEADERS, timeout=15)
if r.status_code == 200 and “<sitemap” in r.text.lower() or “<url” in r.text.lower():
print(f”[OK] Sitemap trovata: {url}”)
return url, r.text
except Exception as e:
print(f”[WARN] {url}: {e}”)
return None, None

def parse_sitemap_urls(xml_text, limit=5):
“”“Estrae URL dalla sitemap XML.”””
locs = re.findall(r”<loc>(.*?)</loc>”, xml_text)
return [l.strip() for l in locs[:limit]]

def is_sitemap_index(xml_text):
“”“Controlla se è un indice di sitemap.”””
return “<sitemap>” in xml_text.lower()

def get_child_sitemaps(xml_text):
“”“Estrae URL delle sitemap figlie.”””
return re.findall(r”<loc>(.*?)</loc>”, xml_text)

def fetch_jina(url):
“”“Fetcha contenuto via Jina Reader.”””
jina_url = f”https://r.jina.ai/{url}”
r = requests.get(jina_url, headers={“Accept”: “text/plain”}, timeout=30)
return r.text if r.status_code == 200 else “”

def analyze_sitemap_structure(xml_text, child_sitemaps):
“”“Analizza la struttura della sitemap per identificare pattern articoli.”””
all_urls = re.findall(r”<loc>(.*?)</loc>”, xml_text)

```
# Conta URL patterns
patterns = {}
for url in all_urls:
    parts = url.split("/")
    if len(parts) > 3:
        key = parts[3] if len(parts) > 3 else "root"
        patterns[key] = patterns.get(key, 0) + 1

return {
    "total_urls": len(all_urls),
    "sample_urls": all_urls[:10],
    "patterns": patterns,
    "child_sitemaps": child_sitemaps[:10] if child_sitemaps else [],
}
```

def call_claude(prompt):
“”“Chiama Claude API.”””
r = requests.post(
“https://api.anthropic.com/v1/messages”,
headers={
“x-api-key”: ANTHROPIC_API_KEY,
“anthropic-version”: “2023-06-01”,
“content-type”: “application/json”,
},
json={
“model”: “claude-sonnet-4-5-20251001”,
“max_tokens”: 8000,
“messages”: [{“role”: “user”, “content”: prompt}],
},
timeout=120,
)
data = r.json()
if “content” in data:
return data[“content”][0][“text”]
print(f”[ERROR] Claude API: {data}”)
return “”

def build_edge_function(site_url, sitemap_info, jina_samples):
“”“Usa Claude per generare la Edge Function.”””
prompt = f””“Sei un esperto di scraping e Supabase Edge Functions (Deno/TypeScript).

Devi generare una Edge Function completa per scaricare articoli da questo sito:
URL: {site_url}

INFORMAZIONI SITEMAP:
{json.dumps(sitemap_info, indent=2)}

CONTENUTO JINA DI UN ARTICOLO CAMPIONE:
{jina_samples[:3000]}

REGOLE OBBLIGATORIE per la Edge Function:

1. Nome funzione: fetch-{site_url.split(”//”)[1].split(”.”)[0].lower().replace(”-”, “”)}
1. max_articles default: 1000
1. Delay tra articoli: 500ms
1. CORS headers completi con Access-Control-Allow-Methods: POST, OPTIONS
1. Early exit se nessun articolo nuovo
1. Hash SHA-256 via crypto.subtle.digest
1. Parametri body: source_id, max_articles (opzionale), dry_run (opzionale)
1. Tabella Supabase: geo_articles con colonne: source_id, url, title, author, original_language, content_original, published_at, scraped_at, url_hash, topic
1. upsert con onConflict: url_hash
1. Aggiorna geo_sources.last_scraped_at e fetcher_status dopo run
1. Inserisce in geo_runs con: started_at, completed_at, sources_total, sources_scraped, articles_found, run_detail
1. Usa createClient da https://esm.sh/@supabase/supabase-js@2
1. Usa Deno.env.get per SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY
1. Filtra solo URL articoli rilevanti (escludi eventi, team, podcast, ecc.)
1. Carica URL gia in DB prima di parsare la sitemap (early exit nel loop)
1. topic default: “General”
1. original_language: “EN”

Analizza il contenuto Jina e determina:

- Quale pattern URL filtrare (es. /article/, /en/comment/, ecc.)
- Come estrarre titolo (H1)
- Come estrarre autore (se presente)
- Come estrarre data pubblicazione
- Dove inizia il contenuto vero
- Quali end markers usano per fermare il parsing

Genera SOLO il codice TypeScript completo della Edge Function, senza spiegazioni, senza markdown backticks.
“””
return call_claude(prompt)

def main():
if len(sys.argv) < 2:
print(“Uso: python3 edge_builder.py https://example.com”)
sys.exit(1)

```
site_url = sys.argv[1].rstrip("/")
site_name = site_url.split("//")[1].split(".")[0].lower().replace("-", "")
output_file = f"fetch-{site_name}.ts"

print(f"\n{'='*60}")
print(f"GeoIntel KB — Edge Builder")
print(f"Sito: {site_url}")
print(f"{'='*60}\n")

# Step 1: Sitemap
print("[1/4] Analisi sitemap...")
sitemap_url, sitemap_xml = fetch_sitemap_index(site_url)
if not sitemap_xml:
    print("[ERROR] Sitemap non trovata. Controlla l'URL.")
    sys.exit(1)

child_sitemaps = []
working_xml = sitemap_xml

if is_sitemap_index(sitemap_xml):
    print("[INFO] Sitemap index trovata — leggo prima sitemap figlia...")
    children = get_child_sitemaps(sitemap_xml)
    child_sitemaps = children
    # Prendi la prima sitemap post/article
    for child in children:
        if "post" in child.lower() or "article" in child.lower() or "publication" in child.lower():
            try:
                r = requests.get(child, headers=HEADERS, timeout=15)
                if r.status_code == 200:
                    working_xml = r.text
                    print(f"[OK] Sitemap figlia: {child}")
                    break
            except:
                pass

sitemap_info = analyze_sitemap_structure(working_xml, child_sitemaps)
print(f"[OK] URL trovati: {sitemap_info['total_urls']}")
print(f"[OK] Pattern principali: {list(sitemap_info['patterns'].keys())[:5]}")

# Step 2: Articolo campione con Jina
print("\n[2/4] Fetch articolo campione via Jina...")
sample_urls = sitemap_info["sample_urls"]
jina_content = ""
for url in sample_urls:
    if any(skip in url for skip in ["/team/", "/event/", "/podcast/", "/media/", "/tag/", "/category/"]):
        continue
    print(f"[INFO] Jina: {url}")
    jina_content = fetch_jina(url)
    if len(jina_content) > 500:
        print(f"[OK] Contenuto: {len(jina_content)} caratteri")
        break

if not jina_content:
    print("[WARN] Jina non ha restituito contenuto utile.")

# Step 3: Genera Edge Function con Claude
print("\n[3/4] Generazione Edge Function con Claude...")
edge_code = build_edge_function(site_url, sitemap_info, jina_content)

if not edge_code or len(edge_code) < 100:
    print("[ERROR] Claude non ha generato codice valido.")
    sys.exit(1)

# Step 4: Salva file
with open(output_file, "w") as f:
    f.write(edge_code)

print(f"\n[4/4] Edge Function salvata: {output_file}")
print(f"\n{'='*60}")
print(f"DONE! File pronto: ~/Documents/{output_file}")
print(f"{'='*60}")
print(f"\nPROSSIMI PASSI:")
print(f"1. Apri {output_file} e verifica il codice")
print(f"2. Deploy su Supabase Edge Functions")
print(f"3. Aggiungi source nell'app GeoIntel KB")
print(f"4. Torna su Claude con UUID per dry run e test")
print(f"{'='*60}\n")
```

if **name** == “**main**”:
main()