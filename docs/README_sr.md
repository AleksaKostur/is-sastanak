# IS SASTANAK

Web informacioni sistem za vođenje sastanaka, saveta, komisija i drugih zvaničnih vidova interakcije zaposlenih u preduzeću, izrađen prema formalnoj specifikaciji.

**Autor:** Aleksa Kostur

English summary: [README.md](../README.md)

---

## Sadržaj

1. [Arhitektura sistema](#1-arhitektura-sistema)
2. [Tehnologije](#2-tehnologije)
3. [Struktura repozitorijuma](#3-struktura-repozitorijuma)
4. [Pokretanje: Docker Compose](#4-pokretanje-docker-compose)
5. [Pokretanje: Kubernetes](#5-pokretanje-kubernetes)
6. [Podešavanje test podataka](#6-podešavanje-test-podataka)
7. [Testiranje](#7-testiranje)
8. [Uloge i pristupna prava (RBAC)](#8-uloge-i-pristupna-prava-rbac)
9. [Ključne poslovne odluke i obrazloženje implementacije](#9-ključne-poslovne-odluke-i-obrazloženje-implementacije)
10. [Pokrivenost projektnog zahteva](#10-pokrivenost-projektnog-zahteva)
11. [Poznata ograničenja](#11-poznata-ograničenja)

---

## 1. Arhitektura sistema

Sistem je podeljen na tri nezavisna REST mikroservisa i jedan frontend, koji dele jednu PostgreSQL bazu podataka.

```
                        ┌────────────────────┐
                        │    React SPA       │
                        │   (Vite + TS)      │   :5173
                        └─────────┬──────────┘
                                  │ REST / JWT
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
     ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
     │  auth-service      │ │ meeting-service    │ │ report-service     │
     │     :8001          │ │     :8002          │ │     :8003          │
     │                    │ │                    │ │                    │
     │ nalozi, uloge,     │ │ sastanci, dnevni   │ │ zapisnici,         │
     │ JWT login/refresh  │ │ red, učesnici,     │ │ izveštaji o        │
     │                    │ │ evidencija,        │ │ učešću, export     │
     │                    │ │ kalendar,          │ │ PDF/XLSX/DOCX      │
     │                    │ │ notifikacije,      │ │                    │
     │                    │ │ eksterna lica      │ │                    │
     └─────────┬──────────┘ └─────────┬──────────┘ └─────────┬──────────┘
               │                      │                      │
               └──────────────────────┼──────────────────────┘
                                      ▼
                             ┌──────────────────┐
                             │    PostgreSQL    │
                             │       :5432      │
                             └──────────────────┘
```

**Zašto podela na baš ova tri servisa:** svaki servis nosi jasno odvojenu odgovornost, identitet i pristup (auth), poslovni proces vođenja sastanka (meeting), generisanje dokumenata i statistike (report). Meeting i report servis dele bazu, ali report servis ne piše u tuđe tabele, samo čita i generiše izlaze, uz svoju `reports` tabelu za evidenciju generisanih dokumenata.

**Autentifikacija između servisa:** svi servisi dele isti `JWT_SECRET`. Auth servis izdaje token, ostala dva ga samo verifikuju lokalno (nema mrežnog poziva ka auth servisu za svaki zahtev), što je brže i otpornije na pad jednog servisa.

**Baza podataka:** jedna PostgreSQL instanca, `docs/schema.sql` je jedini vlasnik šeme. Nijedan servis ne poziva `Base.metadata.create_all()`, šema se učitava isključivo iz `schema.sql` pri prvom podizanju kontejnera baze. Meeting i report servis imaju takozvane mirror SQLAlchemy modele za tabele auth servisa (`users`, `org_units`), koje čitaju ali ne kreiraju niti menjaju.

---

## 2. Tehnologije

Izbor tehnologija prati preporučene varijante iz specifikacije gde god je ona nudila izbor.

| Sloj | Tehnologija | Varijanta |
|---|---|---|
| Baza podataka | PostgreSQL 16 | |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 | primarno, business logika van baze |
| Autentifikacija | JWT (access + refresh token), bcrypt | |
| Mikroservisi | 3 nezavisna REST servisa, 42 endpointa | primarno, minimum 3 zahtevana |
| Frontend | React 19 + TypeScript, Vite, React Router | primarno, napredna web tehnologija |
| Kontejnerizacija | Docker, Docker Compose | primarno |
| Orkestracija | Kubernetes (Deployment + Service za svaki servis) | primarno, dodatak uz Docker |
| Export dokumenata | reportlab (PDF), openpyxl (XLSX), python-docx (DOCX) | |
| Testiranje | pytest, httpx, in-memory SQLite za izolovane testove | dodatni segment |
| Vođenje projekta | Git, GitHub Projects (Scrum board) | |

---

## 3. Struktura repozitorijuma

```
is-sastanak/
├── docs/
│   ├── dijagrami/              use-case, kontekst, DFD, dekompozicija (PNG)
│   ├── erd.dbml, erd.png       ER dijagram baze
│   ├── matrica_uloga.xlsx      RBAC matrica (funkcionalnost x uloga)
│   ├── struktura_proizvoda.xlsx
│   └── schema.sql              jedini izvor šeme baze
├── services/
│   ├── auth-service/           nalozi, uloge, JWT
│   ├── meeting-service/        sastanci, dnevni red, evidencija, kalendar, eksterna lica
│   └── report-service/         zapisnici, izveštaji, export
├── frontend/                   React + TypeScript SPA
├── k8s/                        Kubernetes manifesti
│   ├── postgres.yaml
│   └── services.yaml
├── docker-compose.yml
└── README.md
```

Svaki servis unutar `services/<ime>/app/` prati isti raspored: `models.py` (SQLAlchemy), `schemas.py` (Pydantic), `dependencies.py` (RBAC), `routers/` (endpointi), `main.py`.

Frontend stranice (`frontend/src/pages/`): LoginPage, DashboardPage, MeetingsPage, MeetingDetailPage, CalendarPage, UsersPage, NotificationsPage, ExternalPersonsPage.

---

## 4. Pokretanje: Docker Compose

Preduslov: Docker Desktop.

```bash
git clone https://github.com/AleksaKostur/is-sastanak.git
cd is-sastanak
docker compose up --build -d
```

Ovo podiže četiri kontejnera.

| Servis | Port | Swagger dokumentacija |
|---|---|---|
| PostgreSQL | 5432 | |
| auth-service | 8001 | http://localhost:8001/docs |
| meeting-service | 8002 | http://localhost:8002/docs |
| report-service | 8003 | http://localhost:8003/docs |

Frontend se pokreće odvojeno (nije u docker-compose, radi u razvojnom režimu).

```bash
cd frontend
npm install
npm run dev
```

Aplikacija je dostupna na **http://localhost:5173**.

Baza se inicijalizuje automatski iz `docs/schema.sql` pri prvom podizanju kontejnera. Za sledeći korak (kreiranje prvog naloga) pogledati [poglavlje 6](#6-podešavanje-test-podataka).

---

## 5. Pokretanje: Kubernetes

Preduslovi: `kubectl`, `minikube`.

```bash
minikube start --driver=docker

# poveži terminal na minikube-ov Docker daemon
minikube docker-env | Invoke-Expression      # PowerShell
# eval $(minikube docker-env)                # bash/zsh

# build image-a direktno u minikube (bez registry-ja)
docker build -t auth-service:latest ./services/auth-service
docker build -t meeting-service:latest ./services/meeting-service
docker build -t report-service:latest ./services/report-service

# šema baze ide u ConfigMap
kubectl create configmap postgres-init --from-file=schema.sql=docs/schema.sql

# deploy
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/services.yaml

kubectl get pods
```

Svih pet Deployment/Service parova (postgres i tri servisa) treba da bude Running.

Pristup servisu, primer za auth-service:

```bash
kubectl port-forward service/auth-service 8001:8001
```

**Napomena:** `imagePullPolicy: Never` u manifestima je namerno, image-i se ne skidaju sa registry-ja nego koriste lokalno build-ovane u minikube-ovom Docker daemon-u. Baza u klasteru nema `PersistentVolumeClaim` (podaci se ne čuvaju između restartova pod-a), što je svesna odluka radi jednostavnosti demo okruženja. Za produkciju bi se dodao PVC.

---

## 6. Podešavanje test podataka

Sistem nema formu za javnu registraciju, naloge kreira administrator, u skladu sa spekom ("Naloge registruje administrator"). Prvi administratorski nalog se zato mora uneti direktno u bazu.

```bash
# 1. Organizaciona celina i šifarnik uloga
docker exec is-sastanak-db-1 psql -U sastanak -d sastanak -c \
  "INSERT INTO org_units (name) VALUES ('Sektor IT');"
docker exec is-sastanak-db-1 psql -U sastanak -d sastanak -c \
  "INSERT INTO roles (name) VALUES ('ADMIN'), ('RUKOVODILAC'), ('ZAPISNICAR'), ('UCESNIK');"

# 2. Hash lozinke (bcrypt)
docker exec is-sastanak-auth-service-1 python3 -c \
  "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt'],deprecated='auto').hash('test123'))"

# 3. Prvi korisnik, zameniti HASH sa izlazom prethodne komande
docker exec is-sastanak-db-1 psql -U sastanak -d sastanak -c \
  "INSERT INTO users (org_unit_id, first_name, father_name, last_name, jmbg, job_title, email, password_hash, is_active) \
   VALUES (1, 'Petar', 'Jovan', 'Petrovic', '1234567890123', 'Inzenjer', 'petar@test.com', 'HASH', true);"

# 4. Dodela ADMIN i RUKOVODILAC uloge
docker exec is-sastanak-db-1 psql -U sastanak -d sastanak -c \
  "INSERT INTO user_roles (user_id, role_id, is_permanent) VALUES (1, 1, true), (1, 2, true);"
```

Prijava: **petar@test.com / test123** na http://localhost:5173

Svi ostali korisnici, kategorije sastanaka i eksterna lica kreiraju se kroz UI (Korisnici, Sastanci, Eksterna lica) jednom kada je prvi administrator prijavljen.

---

## 7. Testiranje

23 automatizovana testa (pytest, in-memory SQLite, ne dira produkcionu bazu).

```bash
cd services/auth-service
pip install -r requirements.txt
python -m pytest tests/ -v          # 12 testova: login, RBAC, eskalacija privilegija

cd ../meeting-service
pip install -r requirements.txt
python -m pytest tests/ -v          # 11 testova: poslovna pravila
```

**Auth servis, 12 testova:** uspešna i neuspešna prijava, zaštita endpointa bez tokena, sadržaj JWT tokena, RBAC pristup po ulozi, zabrana čitanja tuđih podataka kroz URL, zabrana samododele ADMIN uloge, validacija obaveznog `org_unit_id` za RUKOVODILAC ulogu.

**Meeting servis, 11 testova:** validacija periodičnosti (stalni/vanredni), RBAC na kreiranju sastanka, pravilo "dnevni red najkasnije 3 dana pre sastanka", pravilo "evidencija prisustva u prozoru od početka sastanka do 72h nakon", klasifikacija matična/druga organizaciona celina, validacija učesnika (interni ili eksterni, ne oba istovremeno).

Testovi nisu deo obaveznog projektnog zahteva, dodati su kao dodatni segment radi provere ispravnosti implementacije, sa fokusom na bezbednosne i poslovne provere koje su najosetljivije na regresiju.

---

## 8. Uloge i pristupna prava (RBAC)

| Funkcionalnost | Admin | Rukovodilac | Zapisničar | Učesnik |
|---|:---:|:---:|:---:|:---:|
| Upravljanje nalozima | X | | | |
| Planiranje sastanka | | X | | |
| Vođenje sastanka | | X | X | |
| Evidencija prisustva | | X | X | |
| Izveštavanje | X | X | X | X |
| Kalendar | X | X | | |
| Notifikacije | X | X | X | X |
| Prijava/odjava | X | X | X | X |

Puna matrica: `docs/matrica_uloga.xlsx`. Implementacija: `dependencies.py` u svakom servisu, kroz FastAPI `Depends()` guardove (`AdminOnly`, `ManagerOrAdmin`, `AnyAuthenticated` i slično), primenjene po istom obrascu u sva tri servisa.

### Zabrana eskalacije privilegija kroz URL

Dva nezavisna sloja zaštite na svakom osetljivom endpointu.

1. **RBAC:** da li token uopšte nosi traženu ulogu, na primer `POST /roles/assign` zahteva ADMIN.
2. **Vlasništvo nad resursom:** da li je korisnik vlasnik konkretnog resursa iz URL-a, na primer `GET /users/{id}` dozvoljava čitanje samo sopstvenih podataka, osim za ADMIN i RUKOVODILAC.

Bez drugog sloja, autentifikovan korisnik bez ikakve uloge mogao bi menjati broj u URL-u (`/users/1`, `/users/2`) i čitati ili menjati tuđe podatke. Provereno testovima `test_user_cannot_read_other_user` i `test_user_cannot_assign_admin_to_self` u `services/auth-service/tests/test_rbac.py`.

---

## 9. Ključne poslovne odluke i obrazloženje implementacije

**Business logika van baze.** `schema.sql` sadrži isključivo `CREATE TABLE` i strane ključeve, nema funkcija, procedura ni trigera. Sva pravila (rok od 3 dana, evidencija u okviru 72h, RBAC, validacije) su u Python kodu servisa. Ovo olakšava testiranje jer se poslovna pravila mogu proveriti bez pokretanja prave baze, kroz in-memory SQLite u testovima.

**Klasifikacija "matična / druga" organizaciona celina** (`services/meeting-service/app/models.py`, `Meeting.classification`) je izvedeno svojstvo, ne kolona u bazi. Računa se poređenjem `meeting.org_unit_id` sa `organizer.org_unit_id` u trenutku čitanja. Razlog: ovaj podatak je uvek jednoznačno određen postojećim podacima (sastanak i njegov organizator), pa bi čuvanje kao zasebna kolona uvelo redundansu i rizik neusklađenosti, na primer da rukovodilac promeni organizacionu celinu posle zakazivanja, a klasifikacija ostane zastarela. Filtriranje po ovom kriterijumu (spek: "sa mogućnošću filtriranja") implementirano je kroz `GET /calendar/?classification=MATICNA` ili `DRUGA`, uz SQL JOIN na tabelu `users`.

**Refresh token sa blacklistom.** Access token važi 30 minuta, refresh token 7 dana. Pri svakom refresh pozivu stari refresh token se stavlja na blacklistu (rotacija tokena), što sprečava ponovnu upotrebu ukradenog refresh tokena. Blacklista je trenutno in-memory `set()` unutar auth servisa. U produkcijskom okruženju bila bi u Redis-u, da preživi restart servisa i da bude deljena između više instanci auth servisa.

**Evidencija prisustva, dvostrani vremenski prozor.** Spek zahteva da se evidencija vrši u toku sastanka ili nakon održavanja, najkasnije 72 sata od kraja sastanka. Implementacija to čita kao dva odvojena uslova: evidencija se odbija (status 400) i ako je pokušana pre `scheduled_at` (sastanak se još nije održao), i ako je pokušana više od 72h posle. Kada su svi planirani učesnici evidentirani, status sastanka se automatski postavlja na ODRZAN, korisnik ne mora ručno da menja status.

**Izveštaj, zaglavlje i podnožje.** Spek: "Evidencija sastanka naznačeno sadrži podatke o rukovodiocu (zaglavlje) i zapisničaru (podnožje)." U generisanim dokumentima (PDF, XLSX, DOCX) ime organizatora se ispisuje na vrhu dokumenta, a zapisničar (prvi učesnik sastanka sa ulogom ZAPISNICAR) na dnu. Potpuni izveštaj (tema, tačke dnevnog reda, izrečeni predlozi sa naznakom ko je koji predlog izneo, zaključak) generiše se kroz isti export endpoint (`GET /reports/meeting/{id}/export`). Predlog bez povezanog aktivnog učesnika u trenutku iznošenja je označen kao "N/A" umesto da izazove grešku.

**Sumarno učešće i izveštaj po korisniku.** Dva odvojena mehanizma: `GET /reports/attendance-summary/me` i `/team` vraćaju brojeve (nedeljno, mesečno, godišnje) za brz pregled na početnoj strani. `GET /reports/attendance-report?period=MONTHLY` ili `YEARLY` generiše preuzimljiv PDF ili XLSX sa temom, dnevnim redom i datumom svakog sastanka na kom je korisnik evidentiran kao prisutan, u skladu sa dva odvojena zahteva iz spek dokumenta.

**Interni i eksterni učesnici.** `MeetingParticipant` ima dva opciona strana ključa, `user_id` (interni) i `external_person_id` (eksterni), sa validacijom da je popunjen tačno jedan od njih (XOR). Eksterna lica se evidentiraju kroz zaseban endpoint (`/meetings/external-persons/create` i `/list`) i posebnu stranicu na frontendu, sa podacima o organizaciji, zemlji i činu, kako spek zahteva za lica van preduzeća. Rute za eksterna lica su namerno registrovane pod `/list` i `/create` sufiksom umesto direktno pod `/external-persons`, kako bi se izbegla kolizija sa putanjom `/meetings/{meeting_id}` u istom routeru (FastAPI bi bez ovoga pokušao da protumači "external-persons" kao vrednost `meeting_id` parametra).

**Zamena učesnika.** `MeetingParticipant.substitute_for_id` je samoreferentna veza na istu tabelu, učesnik koji je zamenio drugog nosi referencu na originalno planiranog učesnika, čime se čuva i ko je bio planiran i ko je stvarno prisustvovao.

**CORS i JWT_SECRET.** Sva tri servisa dele identičan `JWT_SECRET` (prosleđen kao promenljiva okruženja), što omogućava da meeting i report servis nezavisno verifikuju token izdat od auth servisa, bez mrežnog poziva unazad. `CORSMiddleware` je eksplicitno ograničen na `http://localhost:5173` (razvojni frontend port), u produkciji bi se promenio na pravi domen.

---

## 10. Pokrivenost projektnog zahteva

### Arhitektonski zahtevi

| Zahtev | Status |
|---|:---:|
| Business logika van baze, bez procedura i trigera | Da |
| React, napredna web tehnologija | Da |
| Docker i Kubernetes | Da |
| Minimum 3 mikroservisa, REST | Da (3 servisa, 42 endpointa) |

### Dodatni zahtevi

| Zahtev | Status | Napomena |
|---|:---:|---|
| Autentifikacija i autorizacija, uz odjavu | Da | JWT access/refresh, blacklist pri logout-u |
| Administracija IS (sistemski deo) | Da | `/users`, `/roles/assign`, dostupno samo ADMIN ulozi |
| Notifikacije o promenama | Da | uspešno, neuspešno, promena od drugog korisnika |
| Validacija podataka pri unosu | Da | na strani klijenta (`utils/validation.ts`) i servera (Pydantic) |
| Paginacija | Da | sastanci, korisnici, kalendar, notifikacije, eksterna lica |
| Izvoz u .pdf, .xls(x), .doc(x) | Da | reportlab, openpyxl, python-docx |
| Zabrana eskalacije privilegija kroz URL | Da | vidi [poglavlje 8](#8-uloge-i-pristupna-prava-rbac) |
| Obrazloženje rešenja | Da | ovaj dokument |

### Funkcionalni zahtevi iz opisa projekta

Svi zahtevi iz poglavlja "Opis projektnog zahteva" su pokriveni: tačke dnevnog reda najkasnije 3 dana pre sastanka, akt (delovodni broj, datum, organizacija), kategorizacija sastanaka, šest tipova periodičnosti stalnih sastanaka, odlaganje i otkazivanje uz obavezno obrazloženje, potpuni podaci o nalogu (organizaciona celina, JMBG, kontakti), stalne i privremene uloge rukovodioca sa napomenom, čin za interne i eksterne učesnike, evidencija zemlje porekla za strana lica, kalendar bez vremenskog ograničenja sa filtriranjem, evidencija prisustva u roku od 72h, zamena učesnika, klasifikacija matična/druga organizaciona celina sa filtriranjem, sumarno i pojedinačno izveštavanje o učešću.

---

## 11. Poznata ograničenja

- Blacklist refresh tokena je in-memory, gubi se pri restartu auth servisa. U produkciji bi bio u Redis-u.
- K8s baza nema PersistentVolumeClaim, podaci se gube pri restartu pod-a. Svesna odluka radi jednostavnosti demo okruženja.
- Prvi administratorski nalog se unosi ručno u bazu (poglavlje 6). Sistem nema formu za samoregistraciju, u skladu sa spekom da naloge registruje isključivo administrator, ali to znači da bootstrap prvog naloga zahteva direktan pristup bazi.
- Vremenske oznake u generisanim dokumentima su u UTC. Frontend prikazuje datume konvertovane u lokalnu vremensku zonu pretraživača, ali oznaka "Generisano" unutar samog PDF ili XLSX fajla je u UTC.
