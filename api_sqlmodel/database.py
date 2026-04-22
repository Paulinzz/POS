from sqlmodel import create_engine, Session, SQLModel

sqlite_dbname = 'database.db'
sql_url = f'sqlite:///{sqlite_dbname}'
args = {"check_same_thread":False}
engine = create_engine(sql_url, connect_args=args)

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
