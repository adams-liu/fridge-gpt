from app.database import connect, init_db


def main() -> None:
    init_db()
    with connect() as connection:
        connection.execute("DELETE FROM checkout_snapshots")
        connection.execute(
            "DELETE FROM sqlite_sequence WHERE name = ?",
            ("checkout_snapshots",),
        )
    print("Deleted all checkout snapshots.")


if __name__ == "__main__":
    main()
