from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    def __repr__(self) -> str:
        s = [f"{k}={self.__getattribute__(k)}" for k in self.__mapper__.attrs.keys()]
        return f"{self.__class__.__name__}({', '.join(sorted(s))})"
