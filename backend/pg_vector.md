# Run in x64 Native Tools Command Prompts (Administrative mode on)

```bash
set "PGROOT=C:\Program Files\PostgreSQL\18"
cd /d "%TEMP%"
git clone --branch v0.8.6 https://github.com/pgvector/pgvector.git pgvector-0.8.6
cd pgvector-0.8.6
nmake /F Makefile.win
nmake /F Makefile.win install
```

# Enable pgvector in your db in a normal terminal

```bash
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d ausa_db -W -c "CREATE EXTENSION IF NOT EXISTS vector;"
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -d ausa_db -W -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"
```
