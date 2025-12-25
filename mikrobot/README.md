# MIKROBOT – Strona studenckiego koła naukowego

Niniejszy projekt zawiera przykładową, w pełni funkcjonalną stronę WWW dla
studenckiego koła naukowego **MIKROBOT**. Strona została przygotowana z myślą o
współczesnych standardach – jest responsywna (dostosowuje się do ekranów
komputerów stacjonarnych i urządzeń mobilnych) dzięki wykorzystaniu
frameworka Bootstrap i elastycznego układu kolumn. Dane o członkach,
projektach, grantach oraz aktualnościach są przechowywane w bazie danych
SQLite, która – zgodnie z dokumentacją SQLite – świetnie sprawdza się w
serwisach o małym i średnim ruchu, a nawet przy konserwatywnym założeniu do
100 000 odsłon dziennie【251968162808596†L78-L86】.

## Struktura projektu

- **app.py** – Główna aplikacja Flask odpowiedzialna za obsługę żądań,
  generowanie podstron, pobieranie danych z bazy i obsługę panelu
  administracyjnego.
- **init_db.py** – Skrypt inicjujący bazę danych (tworzy tabele i wstawia
  przykładowe dane). Uruchom go przed pierwszym startem aplikacji.
- **mikrobot.db** – Plik bazy danych SQLite generowany po uruchomieniu
  `init_db.py`. Można go usunąć i wygenerować ponownie.
- **templates/** – Katalog z szablonami Jinja2 używanymi przez Flask do
  generowania stron HTML. Podstawowy układ znajduje się w `layout.html`, a
  poszczególne widoki w pozostałych plikach.
- **static/** – Zasoby statyczne: arkusze CSS, skrypty JS (jeśli zajdzie
  potrzeba) oraz obrazy. Katalog `images/` zawiera przykładowe grafiki
  wygenerowane programowo – można je zastąpić własnymi zdjęciami. Własne
  style można dopisać w `css/styles.css`.
- **requirements.txt** – Lista zależności Pythonowych. Instalację wykonaj za
  pomocą `pip install -r requirements.txt`.

## Uruchomienie

1. Upewnij się, że masz zainstalowanego Pythona 3. W środowisku wirtualnym
   (rekomendowane) zainstaluj wymagane pakiety:

   ```bash
   python -m venv venv
   source venv/bin/activate  # w systemie Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Zainicjalizuj bazę danych (utworzy się plik `mikrobot.db` z
   przykładowymi rekordami):

   ```bash
   python init_db.py
   ```

3. Uruchom serwer deweloperski Flask:

   ```bash
   python app.py
   ```

4. Otwórz przeglądarkę i przejdź pod adres `http://127.0.0.1:5000/`.

## Panel administracyjny

Pod adresem `/admin` dostępny jest prosty panel dodawania aktualności. W
produktowym wdrożeniu należy zaimplementować mechanizm logowania i
autoryzacji – w przykładzie panel jest dostępny bez zabezpieczeń w celu
demonstracji. Podczas dodawania aktualności formularz pobiera tytuł i treść,
ustawiając automatycznie datę publikacji na bieżącą. Wpisy trafiają do
tabeli `news` w bazie danych.

## Zmiana treści i rozbudowa

Wszystkie dane (członkowie, projekty, granty, aktualności) znajdują się w
bazie danych i można je łatwo edytować za pomocą skryptu lub panelu
administracyjnego. Szablony stron można modyfikować zgodnie z potrzebami.

## Wykorzystane technologie

- **Flask** – Lekki i elastyczny mikro‑framework Python, który pozwala
  deweloperom dobierać biblioteki i rozszerzenia według potrzeb projektu. Jego
  mechanizm routingu oparty na dekoratorach oraz integracja z silnikiem
  szablonów Jinja2 umożliwiają tworzenie dynamicznych stron internetowych
  w sposób intuicyjny【292461074855809†L87-L100】.
- **Bootstrap** – Szablon CSS/JS umożliwiający tworzenie responsywnych stron
  zgodnie z ideą mobile‑first. Biblioteka zawiera system siatki flexbox,
  dzięki któremu układ dostosowuje się do różnych rozmiarów ekranu【279740201487843†L165-L199】.
  Według dokumentacji Bootstrap 3 mobilne style są „od początku wbudowane w
  rdzeń” frameworka【497221265687908†L45-L52】, a odpowiedni tag viewport w
  `<head>` gwarantuje poprawne skalowanie na urządzeniach mobilnych【497221265687908†L53-L54】.
- **SQLite** – Lekka, prosta baza danych w jednym pliku. Dokumentacja
  wskazuje, że SQLite doskonale sprawdza się jako silnik bazodanowy dla
  większości serwisów o małym i średnim ruchu (do ok. 100 tys. zapytań
  dziennie)【251968162808596†L78-L86】.

Projekt ten stanowi przykład i bazę do dalszej rozbudowy. Możesz dodać
autoryzację, panel zarządzania użytkownikami, stronę galerii czy
formularz kontaktowy wysyłający wiadomości e‑mail.
