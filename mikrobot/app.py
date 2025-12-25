#!/usr/bin/env python3
"""
Główna aplikacja Flask dla strony koła naukowego MIKROBOT.

Flask jest lekki i elastyczny, dzięki czemu możemy zbudować dynamiczny serwis
internetowy, wykorzystując wbudowany mechanizm routingu oparty na dekoratorach
oraz silnik szablonów Jinja2【292461074855809†L87-L100】. Strona korzysta z bazy
danych SQLite, która doskonale sprawdza się w serwisach o niewielkim i
średnim natężeniu ruchu【251968162808596†L78-L86】. Układ strony jest
responsywny dzięki frameworkowi Bootstrap, którego siatka flexbox pozwala
na dostosowanie treści do różnych rozmiarów ekranu【279740201487843†L165-L199】.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "mikrobot.db"

# Directory for uploaded news images (inside the static folder)
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

# Hasło do panelu administracyjnego; w realnej instalacji należy je zmienić
ADMIN_PASSWORD = "admin123"


def get_db_connection():
    """Zwraca połączenie do bazy danych z ustawioną fabryką wierszy."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config["SECRET_KEY"] = "very-secret-key"  # potrzebne do flashowania komunikatów

# Configure upload folder in Flask
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename: str) -> bool:
    """Sprawdza, czy przesłany plik ma dozwolone rozszerzenie"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def inject_now():
    """Wstawia bieżący rok oraz stan logowania do kontekstu szablonów."""
    return {
        "year": datetime.now().year,
        # Umożliwia sprawdzenie w szablonie, czy administrator jest zalogowany
        "admin_logged_in": session.get("admin_logged_in", False),
    }


@app.route("/")
def index():
    """Strona główna – wyświetla najnowsze aktualności."""
    conn = get_db_connection()
    # Pobierz najnowsze 5 aktualności wraz z listą powiązanych obrazów i liczbą obrazów
    news = conn.execute(
        """
        SELECT n.id, n.title, n.content, n.date_posted, n.image,
               GROUP_CONCAT(ni.filename) AS images,
               COUNT(ni.id) AS images_count
        FROM news n
        LEFT JOIN news_images ni ON ni.news_id = n.id
        GROUP BY n.id
        ORDER BY n.date_posted DESC, n.id DESC
        LIMIT 5
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", news=news)


@app.route("/about")
def about():
    """Podstrona opisująca koło naukowe."""
    return render_template("about.html")


@app.route("/members")
def members():
    """Wyświetla członków koła podzielonych na kategorie (opiekunowie, zarząd, członkowie)."""
    conn = get_db_connection()
    # Pobierz wszystkich członków i zgrupuj według kategorii
    rows = conn.execute("SELECT * FROM members ORDER BY id").fetchall()
    conn.close()
    categories = {
        "opiekun": [],
        "zarząd": [],
        "członek": [],
    }
    for row in rows:
        cat = row["category"] if row["category"] in categories else "członek"
        categories[cat].append(row)
    return render_template("members.html", categories=categories)


@app.route("/projects")
def projects():
    """Adres /projects został zastąpiony osiągnięciami – przekieruj na /achievements."""
    # Projekty zostały włączone do osiągnięć. Przekieruj użytkownika do listy osiągnięć.
    return redirect(url_for("achievements"))


@app.route("/grants")
def grants():
    """Adres /grants został zastąpiony osiągnięciami – przekieruj na /achievements."""
    # Granty zostały włączone do osiągnięć. Przekieruj użytkownika do listy osiągnięć.
    return redirect(url_for("achievements"))


@app.route("/news")
def all_news():
    """Strona wyświetlająca wszystkie aktualności."""
    conn = get_db_connection()
    # Pobierz wszystkie aktualności wraz z listą obrazów i liczbą obrazów
    news_list = conn.execute(
        """
        SELECT n.id, n.title, n.content, n.date_posted, n.image,
               GROUP_CONCAT(ni.filename) AS images,
               COUNT(ni.id) AS images_count
        FROM news n
        LEFT JOIN news_images ni ON ni.news_id = n.id
        GROUP BY n.id
        ORDER BY n.date_posted DESC, n.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("news.html", news=news_list)


@app.route("/achievements")
def achievements():
    """Wyświetla listę osiągnięć oraz publikacji wraz z podglądem zdjęć."""
    conn = get_db_connection()
    # Pobierz osiągnięcia wraz z listą wszystkich obrazów (łączonych przecinkiem).
    # Używamy GROUP_CONCAT, aby przekazać pełną listę zdjęć do szablonu. Pierwszy
    # element listy zostanie wyświetlony jako podgląd, a jeśli jest więcej
    # obrazów, skrypt JavaScript zrealizuje pokaz slajdów.
    achievements_list = conn.execute(
        """
        SELECT a.id, a.title, a.description, a.date,
               GROUP_CONCAT(ai.filename) AS images
        FROM achievements a
        LEFT JOIN achievement_images ai ON ai.achievement_id = a.id
        GROUP BY a.id
        ORDER BY a.date DESC, a.id DESC
        """
    ).fetchall()
    # Pobierz publikacje wraz z listą wszystkich obrazów (łączonych przecinkiem)
    publications_list = conn.execute(
        """
        SELECT p.id, p.title, p.description, p.date,
               GROUP_CONCAT(pi.filename) AS images
        FROM publications p
        LEFT JOIN publication_images pi ON pi.publication_id = p.id
        GROUP BY p.id
        ORDER BY p.date DESC, p.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("achievements.html", achievements=achievements_list, publications=publications_list)


@app.route("/skrwaw/members", methods=["GET", "POST"])
def admin_members():
    """Panel zarządzania członkami – dodawanie oraz lista z opcjami edycji i usuwania."""
    # Sprawdź uprawnienia administratora
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    # Upewnij się, że katalog upload istnieje
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        description = request.form.get("description")
        uploaded_file = request.files.get("photo")
        if not name or not role or not description:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            category = request.form.get("category")
            if not category:
                flash("Wybierz kategorię.", "warning")
                return redirect(url_for("admin_members"))
            photo_filename = None
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                if allowed_file(filename):
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    name_part, ext = filename.rsplit('.', 1)
                    unique_filename = f"member_{timestamp}.{ext.lower()}"
                    save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                    uploaded_file.save(save_path)
                    photo_filename = f"uploads/{unique_filename}"
                else:
                    flash("Niedozwolony format pliku.", "warning")
                    return redirect(url_for("admin_members"))
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO members (name, role, description, photo, category) VALUES (?, ?, ?, ?, ?)",
                (name.strip(), role.strip(), description.strip(), photo_filename or "", category)
            )
            conn.commit()
            conn.close()
            flash("Członek dodany pomyślnie!", "success")
            return redirect(url_for("admin_members"))
    # Pobierz listę członków
    conn = get_db_connection()
    members_list = conn.execute("SELECT * FROM members ORDER BY id").fetchall()
    conn.close()
    return render_template("admin_members.html", members=members_list)


@app.route("/skrwaw/members/edit/<int:member_id>", methods=["GET", "POST"])
def edit_member(member_id: int):
    """Edytuj dane członka koła."""
    # Sprawdź, czy administrator jest zalogowany
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        conn.close()
        flash("Nie znaleziono podanego członka.", "danger")
        return redirect(url_for("admin_members"))
    if request.method == "POST":
        name = request.form.get("name")
        role = request.form.get("role")
        description = request.form.get("description")
        uploaded_file = request.files.get("photo")
        if not name or not role or not description:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            category = request.form.get("category")
            if not category:
                flash("Wybierz kategorię.", "warning")
                conn.close()
                return redirect(url_for("edit_member", member_id=member_id))
            photo_filename = member["photo"]
            # Obsłuż ewentualną zmianę zdjęcia
            if uploaded_file and uploaded_file.filename:
                filename = secure_filename(uploaded_file.filename)
                if allowed_file(filename):
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    name_part, ext = filename.rsplit('.', 1)
                    unique_filename = f"member_{timestamp}.{ext.lower()}"
                    save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                    uploaded_file.save(save_path)
                    new_photo_path = f"uploads/{unique_filename}"
                    # Usuń stary plik jeśli istniał
                    if photo_filename:
                        old_path = BASE_DIR / "static" / photo_filename
                        try:
                            old_path.unlink()
                        except FileNotFoundError:
                            pass
                    photo_filename = new_photo_path
                else:
                    flash("Niedozwolony format pliku.", "warning")
                    conn.close()
                    return redirect(url_for("edit_member", member_id=member_id))
            # Aktualizuj wiersz wraz z kategorią
            conn.execute(
                "UPDATE members SET name = ?, role = ?, description = ?, photo = ?, category = ? WHERE id = ?",
                (name.strip(), role.strip(), description.strip(), photo_filename or "", category, member_id)
            )
            conn.commit()
            conn.close()
            flash("Dane członka zaktualizowane pomyślnie!", "success")
            return redirect(url_for("admin_members"))
    conn.close()
    return render_template("edit_member.html", member=member)


@app.route("/skrwaw/members/delete/<int:member_id>", methods=["POST"])
def delete_member(member_id: int):
    """Usuwa członka koła po zalogowaniu administratora."""
    # Sprawdź uprawnienia
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    member = conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()
    if not member:
        conn.close()
        flash("Nie znaleziono podanego członka.", "danger")
        return redirect(url_for("admin_members"))
    # Usuń zdjęcie, jeśli istnieje
    if member["photo"]:
        photo_path = BASE_DIR / "static" / member["photo"]
        try:
            photo_path.unlink()
        except FileNotFoundError:
            pass
    conn.execute("DELETE FROM members WHERE id = ?", (member_id,))
    conn.commit()
    conn.close()
    flash("Członek został usunięty.", "success")
    return redirect(url_for("admin_members"))


@app.route("/skrwaw/achievements", methods=["GET", "POST"])
def admin_achievements():
    """Panel zarządzania osiągnięciami – dodawanie nowych oraz lista z edycją i usuwaniem."""
    # Panel osiągnięć wymaga logowania
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    # Upewnij się, że katalog upload istnieje
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date_str = request.form.get("date")
        uploaded_files = request.files.getlist("images")
        if not title or not description or not date_str:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO achievements (title, description, date) VALUES (?, ?, ?)",
                (title.strip(), description.strip(), date_str.strip())
            )
            achievement_id = cur.lastrowid
            # Zapisz wiele obrazów
            for uploaded_file in uploaded_files:
                if uploaded_file and uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    if allowed_file(filename):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = filename.rsplit('.', 1)
                        unique_filename = f"ach_{achievement_id}_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        uploaded_file.save(save_path)
                        image_rel_path = f"uploads/{unique_filename}"
                        cur.execute(
                            "INSERT INTO achievement_images (achievement_id, filename) VALUES (?, ?)",
                            (achievement_id, image_rel_path)
                        )
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie.", "warning")
                        conn.rollback()
                        conn.close()
                        return redirect(url_for("admin_achievements"))
            conn.commit()
            conn.close()
            flash("Osiągnięcie dodane pomyślnie!", "success")
            return redirect(url_for("admin_achievements"))
    # Pobierz listę osiągnięć wraz z liczbą obrazów
    conn = get_db_connection()
    achievements_list = conn.execute(
        """
        SELECT a.id, a.title, a.description, a.date, COUNT(ai.id) AS images_count
        FROM achievements a
        LEFT JOIN achievement_images ai ON ai.achievement_id = a.id
        GROUP BY a.id
        ORDER BY a.date DESC, a.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin_achievements.html", achievements=achievements_list)


@app.route("/skrwaw/achievements/edit/<int:achievement_id>", methods=["GET", "POST"])
def edit_achievement(achievement_id: int):
    """Edytuj osiągnięcie: zmiana tytułu, opisu, roku i dodawanie kolejnych zdjęć."""
    # Panel edycji osiągnięcia wymaga logowania
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    cur = conn.cursor()
    achievement = cur.execute(
        "SELECT * FROM achievements WHERE id = ?", (achievement_id,)
    ).fetchone()
    if not achievement:
        conn.close()
        flash("Nie znaleziono podanego osiągnięcia.", "danger")
        return redirect(url_for("admin_achievements"))
    # Pobierz powiązane obrazy
    images = cur.execute(
        "SELECT id, filename FROM achievement_images WHERE achievement_id = ? ORDER BY id",
        (achievement_id,)
    ).fetchall()
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date_str = request.form.get("date")
        uploaded_files = request.files.getlist("images")
        if not title or not description or not date_str:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            # Aktualizuj rekord z nową datą (łańcuch tekstowy)
            cur.execute(
                "UPDATE achievements SET title = ?, description = ?, date = ? WHERE id = ?",
                (title.strip(), description.strip(), date_str.strip(), achievement_id)
            )
            # Dodaj nowe pliki, jeśli są przesłane
            for uploaded_file in uploaded_files:
                if uploaded_file and uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    if allowed_file(filename):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = filename.rsplit('.', 1)
                        unique_filename = f"ach_{achievement_id}_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        uploaded_file.save(save_path)
                        image_rel_path = f"uploads/{unique_filename}"
                        cur.execute(
                            "INSERT INTO achievement_images (achievement_id, filename) VALUES (?, ?)",
                            (achievement_id, image_rel_path)
                        )
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie.", "warning")
                        conn.rollback()
                        conn.close()
                        return redirect(url_for("edit_achievement", achievement_id=achievement_id))
            conn.commit()
            conn.close()
            flash("Osiągnięcie zaktualizowane pomyślnie!", "success")
            return redirect(url_for("admin_achievements"))
    conn.close()
    return render_template("edit_achievement.html", achievement=achievement, images=images)


@app.route("/skrwaw/achievements/delete/<int:achievement_id>", methods=["POST"])
def delete_achievement(achievement_id: int):
    """Usuwa osiągnięcie i wszystkie powiązane z nim zdjęcia."""
    # Sprawdź logowanie
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz obrazy, aby usunąć pliki
    images = conn.execute(
        "SELECT filename FROM achievement_images WHERE achievement_id = ?",
        (achievement_id,)
    ).fetchall()
    for row in images:
        if row["filename"]:
            image_path = BASE_DIR / "static" / row["filename"]
            try:
                image_path.unlink()
            except FileNotFoundError:
                pass
    # Usuń rekord w achievements (ON DELETE CASCADE usuwa powiązane obrazy)
    conn.execute("DELETE FROM achievements WHERE id = ?", (achievement_id,))
    conn.commit()
    conn.close()
    flash("Osiągnięcie usunięte pomyślnie!", "success")
    return redirect(url_for("admin_achievements"))


@app.route("/skrwaw/achievements/delete_image/<int:image_id>", methods=["POST"])
def delete_achievement_image(image_id: int):
    """Usuwa pojedyncze zdjęcie powiązane z osiągnięciem."""
    # Wymagane jest zalogowanie, aby uniknąć przypadkowego usunięcia
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz obraz
    row = conn.execute(
        "SELECT achievement_id, filename FROM achievement_images WHERE id = ?",
        (image_id,)
    ).fetchone()
    if not row:
        conn.close()
        flash("Nie znaleziono zdjęcia.", "danger")
        return redirect(url_for("admin_achievements"))
    # Usuń plik
    if row["filename"]:
        image_path = BASE_DIR / "static" / row["filename"]
        try:
            image_path.unlink()
        except FileNotFoundError:
            pass
    # Usuń rekord
    conn.execute("DELETE FROM achievement_images WHERE id = ?", (image_id,))
    conn.commit()
    achievement_id = row["achievement_id"]
    conn.close()
    flash("Zdjęcie zostało usunięte.", "success")
    return redirect(url_for("edit_achievement", achievement_id=achievement_id))


@app.route("/statute")
def statute():
    """Strona z tekstem statutu koła."""
    return render_template("statute.html")


@app.route("/contact")
def contact():
    """Dane kontaktowe i formularz kontaktowy (do rozwinięcia)."""
    return render_template("contact.html")


@app.route("/skrwaw/news", methods=["GET", "POST"])
def admin_news():
    """Panel zarządzania aktualnościami: dodawanie, edycja, usuwanie."""
    # Dostęp tylko dla zalogowanego administratora
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    # Upewnij się, że folder na pliki istnieje
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        uploaded_files = request.files.getlist("images")
        if not title or not content:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            images_to_insert = []
            first_image = None
            # Przetwarzanie wielu plików (jeśli przesłane)
            for file in uploaded_files:
                if file and file.filename:
                    fname = secure_filename(file.filename)
                    if allowed_file(fname):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = fname.rsplit('.', 1)
                        unique_filename = f"news_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        file.save(save_path)
                        rel_path = f"uploads/{unique_filename}"
                        # Zapisz pierwszy obraz jako miniaturę w tabeli news
                        if not first_image:
                            first_image = rel_path
                        images_to_insert.append(rel_path)
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie. Dozwolone: png, jpg, jpeg, gif.", "warning")
                        conn.close()
                        return redirect(url_for("admin_news"))
            # Wstaw wpis do tabeli news z datą aktualną (bez czasu) i miniaturą (może być None)
            cur.execute(
                "INSERT INTO news (title, content, date_posted, image) VALUES (?, ?, ?, ?)",
                (title.strip(), content.strip(), datetime.now().strftime("%Y-%m-%d"), first_image),
            )
            news_id = cur.lastrowid
            # Zapisz wszystkie obrazy do tabeli news_images
            for rel_path in images_to_insert:
                cur.execute(
                    "INSERT INTO news_images (news_id, filename) VALUES (?, ?)",
                    (news_id, rel_path)
                )
            conn.commit()
            conn.close()
            flash("Aktualność dodana pomyślnie!", "success")
            return redirect(url_for("admin_news"))
    # Przy GET lub po zakończonej operacji – wyświetl listę aktualności wraz z liczbą zdjęć
    conn = get_db_connection()
    news_list = conn.execute(
        """
        SELECT n.id, n.title, n.content, n.date_posted, n.image, COUNT(ni.id) AS images_count
        FROM news n
        LEFT JOIN news_images ni ON ni.news_id = n.id
        GROUP BY n.id
        ORDER BY n.date_posted DESC, n.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin_news.html", news=news_list)


@app.route("/skrwaw/news/edit/<int:news_id>", methods=["GET", "POST"])
def edit_news(news_id: int):
    """Edytuje wybraną aktualność. Pozwala zmienić tytuł, treść oraz obraz."""
    # Dostęp tylko dla zalogowanego administratora
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    cur = conn.cursor()
    # Pobierz aktualność
    news_item = cur.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not news_item:
        conn.close()
        flash("Nie znaleziono podanej aktualności.", "danger")
        return redirect(url_for("admin_news"))
    # Pobierz powiązane obrazy
    images = cur.execute(
        "SELECT id, filename FROM news_images WHERE news_id = ? ORDER BY id",
        (news_id,)
    ).fetchall()
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        uploaded_files = request.files.getlist("images")
        if not title or not content:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            # Aktualizuj tytuł i treść
            cur.execute(
                "UPDATE news SET title = ?, content = ? WHERE id = ?",
                (title.strip(), content.strip(), news_id),
            )
            # Obsłuż nowe pliki: zapisuj i dodawaj do tabeli; pierwszy nowy obraz staje się miniaturą w tabeli news
            new_image_thumbnail = None
            for file in uploaded_files:
                if file and file.filename:
                    fname = secure_filename(file.filename)
                    if allowed_file(fname):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = fname.rsplit('.', 1)
                        unique_filename = f"news_{news_id}_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        file.save(save_path)
                        rel_path = f"uploads/{unique_filename}"
                        # Jeśli to pierwszy z nowych plików, zaktualizuj miniaturę w news
                        if not new_image_thumbnail:
                            new_image_thumbnail = rel_path
                        cur.execute(
                            "INSERT INTO news_images (news_id, filename) VALUES (?, ?)",
                            (news_id, rel_path),
                        )
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie.", "warning")
                        conn.rollback()
                        conn.close()
                        return redirect(url_for("edit_news", news_id=news_id))
            # Jeśli dodano nowy obraz miniatury, usuń poprzednią miniaturę (o ile nie jest w tabeli news_images)
            if new_image_thumbnail:
                # Usuń stary plik graficzny, jeśli istnieje i jeśli nie należy do news_images
                old_image = news_item["image"]
                if old_image:
                    # Sprawdź, czy stary plik jest zapisany w news_images; jeśli tak, nie usuwaj go podwójnie
                    cur2 = conn.cursor()
                    existing = cur2.execute(
                        "SELECT 1 FROM news_images WHERE news_id = ? AND filename = ?",
                        (news_id, old_image),
                    ).fetchone()
                    if not existing:
                        old_path = BASE_DIR / "static" / old_image
                        try:
                            old_path.unlink()
                        except FileNotFoundError:
                            pass
                # Zaktualizuj miniaturę w tabeli news
                cur.execute(
                    "UPDATE news SET image = ? WHERE id = ?",
                    (new_image_thumbnail, news_id),
                )
            conn.commit()
            conn.close()
            flash("Aktualność zaktualizowana pomyślnie!", "success")
            return redirect(url_for("admin_news"))
    conn.close()
    return render_template("edit_news.html", news_item=news_item, images=images)


@app.route("/skrwaw/news/delete/<int:news_id>", methods=["POST"])
def delete_news(news_id: int):
    """Usuwa wskazaną aktualność. Operacja wymaga zalogowanego administratora."""
    # Sprawdź, czy administrator jest zalogowany
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz wiersz, aby ewentualnie usunąć powiązane pliki
    news_item = conn.execute("SELECT * FROM news WHERE id = ?", (news_id,)).fetchone()
    if not news_item:
        conn.close()
        flash("Nie znaleziono podanej aktualności.", "danger")
        return redirect(url_for("admin_news"))
    # Usuń wszystkie powiązane obrazy (z tabeli news_images)
    images = conn.execute(
        "SELECT filename FROM news_images WHERE news_id = ?",
        (news_id,)
    ).fetchall()
    for row in images:
        if row["filename"]:
            img_path = BASE_DIR / "static" / row["filename"]
            try:
                img_path.unlink()
            except FileNotFoundError:
                pass
    # Usuń miniaturę zapisane w kolumnie image, jeśli nie znajduje się w news_images (może być duplikatem)
    if news_item["image"]:
        # Sprawdź, czy plik jest w news_images; jeśli nie, usuń
        in_table = conn.execute(
            "SELECT 1 FROM news_images WHERE news_id = ? AND filename = ?",
            (news_id, news_item["image"]),
        ).fetchone()
        if not in_table:
            thumb_path = BASE_DIR / "static" / news_item["image"]
            try:
                thumb_path.unlink()
            except FileNotFoundError:
                pass
    # Usuń wiersz z bazy (powiązane rekordy w news_images zostaną usunięte dzięki ON DELETE CASCADE)
    conn.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()
    flash("Aktualność usunięta pomyślnie!", "success")
    return redirect(url_for("admin_news"))


@app.route("/skrwaw/news/delete_image/<int:image_id>", methods=["POST"])
def delete_news_image(image_id: int):
    """Usuwa pojedyncze zdjęcie powiązane z aktualnością."""
    # Wymagane jest zalogowanie, aby uniknąć przypadkowego usunięcia
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz obraz
    row = conn.execute(
        "SELECT news_id, filename FROM news_images WHERE id = ?",
        (image_id,),
    ).fetchone()
    if not row:
        conn.close()
        flash("Nie znaleziono zdjęcia.", "danger")
        return redirect(url_for("admin_news"))
    # Usuń plik z dysku
    if row["filename"]:
        image_path = BASE_DIR / "static" / row["filename"]
        try:
            image_path.unlink()
        except FileNotFoundError:
            pass
    # Usuń rekord z bazy
    conn.execute("DELETE FROM news_images WHERE id = ?", (image_id,))
    # Jeśli usunięte zdjęcie było również miniaturą w tabeli news, zaktualizuj miniaturę na inny obraz lub NULL
    news_id = row["news_id"]
    # Sprawdź, czy ten plik był przypisany jako miniatura
    cur = conn.cursor()
    # Pobierz bieżącą miniaturę
    current_thumb = cur.execute(
        "SELECT image FROM news WHERE id = ?",
        (news_id,),
    ).fetchone()
    if current_thumb and current_thumb[0] == row["filename"]:
        # Znajdź inny obraz powiązany z aktualnością, aby ustawić go jako miniaturę
        new_thumb = cur.execute(
            "SELECT filename FROM news_images WHERE news_id = ? ORDER BY id LIMIT 1",
            (news_id,),
        ).fetchone()
        if new_thumb:
            cur.execute(
                "UPDATE news SET image = ? WHERE id = ?",
                (new_thumb[0], news_id),
            )
        else:
            # Brak innych obrazów – ustaw miniaturę na NULL
            cur.execute(
                "UPDATE news SET image = NULL WHERE id = ?",
                (news_id,),
            )
    conn.commit()
    conn.close()
    flash("Zdjęcie zostało usunięte.", "success")
    return redirect(url_for("edit_news", news_id=news_id))


# Wylogowanie z panelu administratora
@app.route("/skrwaw/logout")
def admin_logout():
    """Kasuje sesję administratora i przekierowuje na stronę logowania."""
    session.pop("admin_logged_in", None)
    flash("Wylogowano pomyślnie!", "info")
    return redirect(url_for("admin_home"))

# Ważne linki – prosta podstrona z odnośnikami do zasobów zewnętrznych lub partnerów
@app.route("/links")
def links():
    """Strona z ważnymi linkami dla członków koła."""
    return render_template("important_links.html")


@app.route("/skrwaw/publications", methods=["GET", "POST"])
def admin_publications():
    """Panel zarządzania publikacjami – dodawanie nowych oraz lista z edycją i usuwaniem."""
    # Sprawdź, czy administrator jest zalogowany
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    # Upewnij się, że katalog upload istnieje
    app.config["UPLOAD_FOLDER"].mkdir(parents=True, exist_ok=True)
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date_str = request.form.get("date")
        uploaded_files = request.files.getlist("images")
        if not title or not description or not date_str:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            # Wstaw nową publikację
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO publications (title, description, date) VALUES (?, ?, ?)",
                (title.strip(), description.strip(), date_str.strip()),
            )
            publication_id = cur.lastrowid
            # Zapisz wiele obrazów, jeśli zostały przesłane
            for uploaded_file in uploaded_files:
                if uploaded_file and uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    if allowed_file(filename):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = filename.rsplit('.', 1)
                        unique_filename = f"pub_{publication_id}_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        uploaded_file.save(save_path)
                        image_rel_path = f"uploads/{unique_filename}"
                        cur.execute(
                            "INSERT INTO publication_images (publication_id, filename) VALUES (?, ?)",
                            (publication_id, image_rel_path),
                        )
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie.", "warning")
                        conn.rollback()
                        conn.close()
                        return redirect(url_for("admin_publications"))
            conn.commit()
            conn.close()
            flash("Publikacja dodana pomyślnie!", "success")
            return redirect(url_for("admin_publications"))
    # Przy GET wyświetl listę publikacji wraz z liczbą zdjęć
    conn = get_db_connection()
    publications_list = conn.execute(
        """
        SELECT p.id, p.title, p.description, p.date, COUNT(pi.id) AS images_count
        FROM publications p
        LEFT JOIN publication_images pi ON pi.publication_id = p.id
        GROUP BY p.id
        ORDER BY p.date DESC, p.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("admin_publications.html", publications=publications_list)


@app.route("/skrwaw/publications/edit/<int:publication_id>", methods=["GET", "POST"])
def edit_publication(publication_id: int):
    """Edytuj publikację: zmiana tytułu, opisu, daty i dodawanie nowych zdjęć."""
    # Wymagane jest zalogowanie
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    cur = conn.cursor()
    publication = cur.execute(
        "SELECT * FROM publications WHERE id = ?", (publication_id,)
    ).fetchone()
    if not publication:
        conn.close()
        flash("Nie znaleziono podanej publikacji.", "danger")
        return redirect(url_for("admin_publications"))
    # Pobierz powiązane obrazy
    images = cur.execute(
        "SELECT id, filename FROM publication_images WHERE publication_id = ? ORDER BY id", (publication_id,)
    ).fetchall()
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        date_str = request.form.get("date")
        uploaded_files = request.files.getlist("images")
        if not title or not description or not date_str:
            flash("Uzupełnij wszystkie pola.", "warning")
        else:
            # Aktualizuj rekord
            cur.execute(
                "UPDATE publications SET title = ?, description = ?, date = ? WHERE id = ?",
                (title.strip(), description.strip(), date_str.strip(), publication_id),
            )
            # Dodaj nowe pliki, jeśli są przesłane
            for uploaded_file in uploaded_files:
                if uploaded_file and uploaded_file.filename:
                    filename = secure_filename(uploaded_file.filename)
                    if allowed_file(filename):
                        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                        name_part, ext = filename.rsplit('.', 1)
                        unique_filename = f"pub_{publication_id}_{timestamp}.{ext.lower()}"
                        save_path = app.config["UPLOAD_FOLDER"] / unique_filename
                        uploaded_file.save(save_path)
                        image_rel_path = f"uploads/{unique_filename}"
                        cur.execute(
                            "INSERT INTO publication_images (publication_id, filename) VALUES (?, ?)",
                            (publication_id, image_rel_path),
                        )
                    else:
                        flash("Jeden z plików ma niedozwolone rozszerzenie.", "warning")
                        conn.rollback()
                        conn.close()
                        return redirect(url_for("edit_publication", publication_id=publication_id))
            conn.commit()
            conn.close()
            flash("Publikacja zaktualizowana pomyślnie!", "success")
            return redirect(url_for("admin_publications"))
    conn.close()
    return render_template("edit_publication.html", publication=publication, images=images)


@app.route("/skrwaw/publications/delete/<int:publication_id>", methods=["POST"])
def delete_publication(publication_id: int):
    """Usuwa publikację i powiązane z nią zdjęcia."""
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz obrazy, aby usunąć pliki z dysku
    images = conn.execute(
        "SELECT filename FROM publication_images WHERE publication_id = ?",
        (publication_id,)
    ).fetchall()
    for row in images:
        if row["filename"]:
            image_path = BASE_DIR / "static" / row["filename"]
            try:
                image_path.unlink()
            except FileNotFoundError:
                pass
    # Usuń rekord z bazy (powiązane obrazy usuwane są przez ON DELETE CASCADE)
    conn.execute("DELETE FROM publications WHERE id = ?", (publication_id,))
    conn.commit()
    conn.close()
    flash("Publikacja została usunięta.", "success")
    return redirect(url_for("admin_publications"))


@app.route("/skrwaw/publications/delete_image/<int:image_id>", methods=["POST"])
def delete_publication_image(image_id: int):
    """Usuwa pojedyncze zdjęcie powiązane z publikacją."""
    if not session.get("admin_logged_in"):
        flash("Zaloguj się do panelu administracyjnego.", "danger")
        return redirect(url_for("admin_home"))
    conn = get_db_connection()
    # Pobierz obraz
    row = conn.execute(
        "SELECT publication_id, filename FROM publication_images WHERE id = ?",
        (image_id,)
    ).fetchone()
    if not row:
        conn.close()
        flash("Nie znaleziono zdjęcia.", "danger")
        return redirect(url_for("admin_publications"))
    # Usuń plik
    if row["filename"]:
        image_path = BASE_DIR / "static" / row["filename"]
        try:
            image_path.unlink()
        except FileNotFoundError:
            pass
    # Usuń rekord z bazy
    conn.execute("DELETE FROM publication_images WHERE id = ?", (image_id,))
    conn.commit()
    publication_id = row["publication_id"]
    conn.close()
    flash("Zdjęcie zostało usunięte.", "success")
    return redirect(url_for("edit_publication", publication_id=publication_id))


# Nowa strona główna panelu administracyjnego: wybór kategorii do zarządzania
# Zmiana ścieżki głównej panelu administracyjnego zgodnie z wymaganiem.
@app.route("/skrwaw", methods=["GET", "POST"])
def admin_home():
    """Panel administracyjny.

    Jeśli użytkownik nie jest zalogowany, wyświetlany jest formularz logowania.
    Po zalogowaniu panel umożliwia wybór kategorii do zarządzania.
    """
    logged_in = session.get("admin_logged_in", False)
    # Obsługa żądania POST
    if request.method == "POST":
        # Jeśli użytkownik nie jest jeszcze zalogowany, traktuj POST jako próbę logowania
        if not logged_in:
            password = request.form.get("password")
            if password == ADMIN_PASSWORD:
                session["admin_logged_in"] = True
                flash("Zalogowano pomyślnie!", "success")
                return redirect(url_for("admin_home"))
            else:
                flash("Nieprawidłowe hasło!", "danger")
        else:
            # Użytkownik jest zalogowany – obsłuż wybór kategorii
            category = request.form.get("category")
            if category == "news":
                return redirect(url_for("admin_news"))
            elif category == "members":
                return redirect(url_for("admin_members"))
            elif category == "achievements":
                return redirect(url_for("admin_achievements"))
            elif category == "publications":
                return redirect(url_for("admin_publications"))
            else:
                flash("Wybierz poprawną kategorię.", "warning")
    # GET lub niepoprawny POST – pokaż stronę
    return render_template("admin_home.html", logged_in=logged_in)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)