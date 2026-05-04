# from sqlalchemy import text
# from db.db import Session as PostgresSession
# from db.db_company import engine as mysql_engine
# from db.models import ScrapedAuthor
# import json

# BATCH_SIZE = 500


# def fetch_authors(pg_session, offset, limit):
#     return (
#         pg_session.query(ScrapedAuthor)
#         .order_by(ScrapedAuthor.id)
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )


# def insert_batch_mysql(records):
#     if not records:
#         return

#     sql = text("""
#         INSERT INTO scraped_author (
#             id,
#             author,
#             about_author,
#             author_birth_date,
#             author_death_date,
#             author_website,
#             author_age,
#             author_current_address,
#             author_candidate_address,
#             book_url,
#             book_title,
#             book_rating,
#             age_and_addr_filled,
#             to_delete,
#             exists_in_company_db,
#             created_at
#         ) VALUES (
#             :id,
#             :author,
#             :about_author,
#             :author_birth_date,
#             :author_death_date,
#             :author_website,
#             :author_age,
#             :author_current_address,
#             :author_candidate_address,
#             :book_url,
#             :book_title,
#             :book_rating,
#             :age_and_addr_filled,
#             :to_delete,
#             :exists_in_company_db,
#             :created_at
#         )
#         ON DUPLICATE KEY UPDATE
#             author = VALUES(author)
#     """)

#     with mysql_engine.begin() as conn:
#         conn.execute(sql, records)


# def migrate():
#     pg_session = PostgresSession()

#     offset = 0
#     total_migrated = 0

#     try:
#         while True:
#             batch = fetch_authors(pg_session, offset, BATCH_SIZE)

#             if not batch:
#                 break

#             records = []
#             for a in batch:
#                 records.append({
#                     "id": a.id,
#                     "author": a.author,
#                     "about_author": a.about_author,
#                     "author_birth_date": a.author_birth_date,
#                     "author_death_date": a.author_death_date,
#                     "author_website": a.author_website,
#                     "author_age": a.author_age,
#                     "author_current_address": a.author_current_address,
#                     "author_candidate_address": json.dumps(a.author_candidate_address or []),
#                     "book_url": a.book_url,
#                     "book_title": a.book_title,
#                     "book_rating": a.book_rating,
#                     "age_and_addr_filled": a.age_and_addr_filled,
#                     "to_delete": a.to_delete,
#                     "exists_in_company_db": a.exists_in_company_db,
#                     "created_at": a.created_at,
#                 })

#             insert_batch_mysql(records)

#             offset += BATCH_SIZE
#             total_migrated += len(records)

#             print(f"Migrated: {total_migrated}")

#         print("✅ Migration complete!")

#     except Exception as e:
#         print(f"❌ Error: {e}")
#         pg_session.rollback()

#     finally:
#         pg_session.close()


# if __name__ == "__main__":
#     migrate()

from sqlalchemy import text
from db.db import Session as PostgresSession
from db.db_company import engine as mysql_engine
from db.models import Lead


BATCH_SIZE = 500


def fetch_leads(pg_session, offset, limit):
    return (
        pg_session.query(Lead)
        .order_by(Lead.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


def insert_leads_mysql(records):
    if not records:
        return

    sql = text("""
        INSERT INTO `lead` (
            id,
            author,
            author_email,
            author_contact_num,
            author_address,
            book_url,
            book_title,
            book_rating,
            information_filled,
            exported,
            exists_in_company_db,
            created_at
        )
        VALUES (
            :id,
            :author,
            :author_email,
            :author_contact_num,
            :author_address,
            :book_url,
            :book_title,
            :book_rating,
            :information_filled,
            :exported,
            :exists_in_company_db,
            :created_at
        )
        ON DUPLICATE KEY UPDATE
            author = VALUES(author),
            book_title = VALUES(book_title)
    """)

    with mysql_engine.begin() as conn:
        conn.execute(sql, records)


def migrate_leads():
    pg_session = PostgresSession()

    offset = 0
    total = 0

    try:
        while True:
            batch = fetch_leads(pg_session, offset, BATCH_SIZE)

            if not batch:
                break

            records = []

            for l in batch:
                records.append({
                    "id": l.id,
                    "author": l.author,
                    "author_email": l.author_email,
                    "author_contact_num": l.author_contact_num,
                    "author_address": l.author_address,
                    "book_url": l.book_url,
                    "book_title": l.book_title,
                    "book_rating": l.book_rating,

                    # IMPORTANT: bool → int for MySQL
                    "information_filled": int(l.information_filled or 0),
                    "exported": int(l.exported or 0),
                    "exists_in_company_db": int(l.exists_in_company_db or 0),

                    "created_at": l.created_at,
                })

            insert_leads_mysql(records)

            offset += BATCH_SIZE
            total += len(records)

            print(f"Migrated leads: {total}")

        print("✅ Lead migration complete!")

    except Exception as e:
        print(f"❌ Error: {e}")
        pg_session.rollback()

    finally:
        pg_session.close()


if __name__ == "__main__":
    migrate_leads()