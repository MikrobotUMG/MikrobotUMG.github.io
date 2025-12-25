#!/usr/bin/env python3
"""
Inicjalizuje bazę danych aplikacji MIKROBOT.

Uruchom ten skrypt przed pierwszym startem aplikacji, aby utworzyć plik
`mikrobot.db` wraz z podstawową strukturą tabel oraz przykładowymi danymi.
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent / "mikrobot.db"


def init_db():
    """Tworzy bazę danych i wstawia przykładowe rekordy."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Włącz obsługę kluczy obcych
    cur.execute("PRAGMA foreign_keys = ON;")

    # Najpierw usuń istniejące tabele, aby móc stworzyć je z aktualnym schematem
    cur.execute("DROP TABLE IF EXISTS members;")
    cur.execute("DROP TABLE IF EXISTS projects;")  # projects are deprecated
    cur.execute("DROP TABLE IF EXISTS achievements;")
    cur.execute("DROP TABLE IF EXISTS achievement_images;")
    cur.execute("DROP TABLE IF EXISTS publications;")
    cur.execute("DROP TABLE IF EXISTS publication_images;")
    cur.execute("DROP TABLE IF EXISTS news;")
    # Tabela news_images może istnieć z poprzednich wersji – usuń ją, aby odtworzyć z nowym schematem
    cur.execute("DROP TABLE IF EXISTS news_images;")
    cur.execute("DROP TABLE IF EXISTS grants;")

    # Tworzenie tabel
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            description TEXT NOT NULL,
            photo TEXT NOT NULL,
            category TEXT NOT NULL
        );
        """
    )


    # Nie tworzymy już tabeli projects – projekty zostały włączone do osiągnięć.

    # Tabela osiągnięć; dawniej granty. Przechowuje tytuł, opis oraz pełną datę (YYYY-MM-DD)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        );
        """
    )

    # Tabela powiązań obrazów z osiągnięciami (możliwe wiele obrazów na jedno osiągnięcie)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS achievement_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            FOREIGN KEY (achievement_id) REFERENCES achievements(id) ON DELETE CASCADE
        );
        """
    )

    # Tabela publikacji wraz z pełną datą. Publikacje mogą posiadać wiele załączonych plików/grafik.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL
        );
        """
    )
    # Tabela powiązań obrazów z publikacjami (możliwe wiele obrazów na jedną publikację)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS publication_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            publication_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            FOREIGN KEY (publication_id) REFERENCES publications(id) ON DELETE CASCADE
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            date_posted TEXT NOT NULL,
            image TEXT
        );
        """
    )

    # Tabela przechowująca wiele zdjęć dla jednej aktualności. Dzięki temu możemy
    # przypisać dowolną liczbę obrazów do wpisu i wyświetlać je jako pokaz
    # slajdów. Klucz obcy z ON DELETE CASCADE sprawia, że usunięcie wpisu
    # spowoduje automatyczne usunięcie powiązanych zdjęć.
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS news_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        );
        """
    )

    # Po utworzeniu tabel nie wykonujemy już operacji DROP/DELETE – zostały wykonane wcześniej

    # Wstaw przykładowych członków z kategoriami. Kategorie: opiekun (dwóch mentorów), zarząd (3 osoby), członek (pozostali)
    members_data = [
        (
            "Dr hab. Ewa Nowicka",
            "Opiekun naukowy",
            "Adiunkt w katedrze automatyki. Specjalistka w dziedzinie sterowania mikrorobotami.",
            "images/team.jpg",
            "opiekun",
        ),
        (
            "Mgr inż. Piotr Kowalczyk",
            "Opiekun naukowy",
            "Wieloletni praktyk inżynierii robotycznej, wspiera koło w sprawach technicznych.",
            "images/team.jpg",
            "opiekun",
        ),
        (
            "Anna Kowalska",
            "Przewodnicząca",
            "Studentka automatyki i robotyki. Interesuje się projektowaniem mikrorobotów i sztuczną inteligencją.",
            "images/team.jpg",
            "zarząd",
        ),
        (
            "Jan Nowak",
            "Wiceprzewodniczący",
            "Entuzjasta elektroniki i programowania mikrokontrolerów. Odpowiada za koordynację projektów.",
            "images/team.jpg",
            "zarząd",
        ),
        (
            "Katarzyna Wiśniewska",
            "Skarbnik",
            "Specjalizuje się w mechanice precyzyjnej oraz druku 3D, prowadzi warsztaty dla nowych członków.",
            "images/team.jpg",
            "zarząd",
        ),
        (
            "Marek Zając",
            "Członek",
            "Student informatyki, pasjonat sztucznej inteligencji i algorytmiki.",
            "images/team.jpg",
            "członek",
        ),
        (
            "Ola Ptak",
            "Członek",
            "Studentka mechatroniki, zajmuje się projektowaniem PCB i montażem urządzeń.",
            "images/team.jpg",
            "członek",
        ),
        (
            "Tomasz Lis",
            "Członek",
            "Hobbystycznie zajmuje się drukiem 3D i programowaniem w Pythonie.",
            "images/team.jpg",
            "członek",
        ),
    ]
    cur.executemany(
        "INSERT INTO members (name, role, description, photo, category) VALUES (?, ?, ?, ?, ?);",
        members_data,
    )

    # Nie wstawiamy przykładowych projektów – projekty zostały połączone z osiągnięciami.

    # Wstaw przykładowe osiągnięcia (dawniej granty)
    achievements_data = [
        (
            "Grant MIN-Robotics",
            "Dofinansowanie z Ministerstwa Nauki na badania nad mikro napędami i układami zasilania.",
            "2024-06-15",
        ),
        (
            "Program Innowacyjny Student",
            "Grant na rozwój projektu MicroDrone w ramach programu Innowacyjny Student.",
            "2023-09-10",
        ),
        (
            "Fundusz Rozwoju Nauki",
            "Środki przeznaczone na budowę zaplecza laboratoryjnego i zakup drukarki 3D o wysokiej rozdzielczości.",
            "2025-05-01",
        ),
    ]
    cur.executemany(
        "INSERT INTO achievements (title, description, date) VALUES (?, ?, ?);",
        achievements_data,
    )

    # Wstaw przykładowe publikacje
    publications_data = [
        (
            "Publikacja w Journal of Microrobotics",
            "Artykuł opisujący wyniki badań nad mikro napędami i sterowaniem.",
            "2023-05-20",
        ),
        (
            "Konferencja RoboTech 2024",
            "Prezentacja osiągnięć koła MIKROBOT podczas konferencji RoboTech.",
            "2024-03-15",
        ),
    ]
    cur.executemany(
        "INSERT INTO publications (title, description, date) VALUES (?, ?, ?);",
        publications_data,
    )

    # Wstaw przykładowe aktualności
    # Ustaw datę (bez czasu) w formacie RRRR-MM-DD dla przykładowych aktualności
    now_str = datetime.now().strftime("%Y-%m-%d")
    # news_data now includes a fourth element (image filename) which can be NULL/None
    news_data = [
        (
            "Start projektu NanoWalker",
            "Rozpoczynamy nowy projekt badawczy NanoWalker. Zapraszamy do współpracy wszystkich zainteresowanych!",
            now_str,
            None
        ),
        (
            "Sukces na konkursie robotycznym",
            "Nasza drużyna zdobyła pierwsze miejsce w konkursie Eurobot Junior dzięki projektowi SmartGrip.",
            now_str,
            None
        ),
        (
            "Warsztaty druku 3D",
            "W przyszłym tygodniu organizujemy warsztaty z druku 3D w naszym laboratorium. Liczba miejsc ograniczona.",
            now_str,
            None
        ),
    ]
    cur.executemany(
        "INSERT INTO news (title, content, date_posted, image) VALUES (?, ?, ?, ?);",
        news_data,
    )

    conn.commit()
    conn.close()
    print(f"Baza danych zainicjalizowana: {DB_PATH}")


if __name__ == "__main__":
    init_db()