from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from libs.get_database_uri import get_database_uri
from libs.logging import get_logger

engine = create_engine(get_database_uri())

Session = sessionmaker(bind=engine)

logger = get_logger(__name__)
logger.setLevel("INFO")


@contextmanager
def session_scope():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"session rollback: {e}")
        raise e
    finally:
        logger.info("session closed")
        session.close()
