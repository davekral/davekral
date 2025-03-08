import sqlite3

# Název souboru databáze
DB_FILE = "users.db"

def show_users_with_passwords():
    try:
        # Připojení k databázi
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Kontrola existence tabulky
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print("Tabulka 'users' neexistuje.")
            return

        # Výpis obsahu tabulky users
        print("Obsah tabulky 'users':")
        cursor.execute("SELECT id, username, password_hash FROM users;")
        rows = cursor.fetchall()

        if rows:
            for row in rows:
                print(f"ID: {row[0]}, Username: {row[1]}, Password Hash: {row[2]}")
        else:
            print("Tabulka je prázdná.")

    except sqlite3.Error as e:
        print(f"Chyba při práci s databází: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    show_users_with_passwords()
