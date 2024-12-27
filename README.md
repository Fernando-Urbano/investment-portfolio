# Investment Portfolio

## Create Virtual Environment
The virtual environment is created using conda. It is used to manage the dependencies of the package.

The following steps are used to create the virtual environment.

Inside your terminal, write:
```bash
conda create -n invp python=3.12.5
```

Activate virtual environment:
```bash
conda activate invp
```

Install packages:
```bash
pip install -r requirements.txt
```

# Start Flask Database

If running the development database:
```bash
export FLASK_APP=development
```

If running the tets database:
```bash
export FLASK_ENV=testing
```

```bash
python -m flask shell
```

Inside the shell:
```
from app import db
db.create_all()
```

After completed:
```
exit()
```

Check that the database has been created by running in the terminal.

In development:
```bash
psql investment_portfolio
```

In testing:
```bash
psql investment_portfolio_test
```

```
\dt
```

The expected output should be:
```
                 List of relations
 Schema |      Name        | Type  | Owner               
--------+------------------+-------+---------------------
 public | asset            | table | fernandorochacorreaurbano
 public | data_point       | table | fernandorochacorreaurbano
 public | time_series      | table | fernandorochacorreaurbano
 public | time_series_type | table | fernandorochacorreaurbano
(4 rows)
```


# Migrations:
If running the development database:
```bash
export FLASK_APP=development
```

If running the tets database:
```bash
export FLASK_ENV=testing
```

Run the following only if there are no initial migrations:
```bash
python -m flask db init
```

Now, regardless of having or not migrated the database, run the following commands:

```bash
python -m flask db migrate -m "comment"
```

```bash
python -m flask db upgrade
```

Check for updates:

In development:
```bash
psql investment_portfolio
```

In testing:
```bash
psql investment_portfolio_test
```

Inside the PostgreSQL shell, check for the available tables:
```
\dt
```

Go inside the desired table:
```
\d asset
```
