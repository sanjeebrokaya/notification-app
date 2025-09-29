PATCH NOTES

1) Replace your project's files with the ones in this patch:
   - index.html (nicer UI)
   - logger-service/app.py (ensures table exists before writes/reads)
   - logger-service/init.sql (auto-creates logs table on first DB start)
   - logger-service/requirements.txt
   - docker-compose.yaml (mounts init.sql into Postgres)

2) If your Postgres volume already exists, init.sql won't run.
   Either reset the volume OR run this one-time command:

   docker compose exec postgres psql -U user -d logs_db -c "DROP TABLE IF EXISTS logs; CREATE TABLE logs (id SERIAL PRIMARY KEY, message TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());"

3) Bring the stack back up:

   docker compose down -v
   docker compose up -d --build

4) Visit index.html, send a message, then see logs.
