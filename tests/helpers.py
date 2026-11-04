from dataclasses import replace
from supermercado.config import Config, Band, Cashier
from supermercado.domain import Customer


def model(boxes=1,end=30,**changes):
    if 'bands' in changes:
        end=changes['bands'][-1].end
    c=Config(bands=(Band('dia',0,end,0,boxes),),days=1,priority_fraction=0,
             cashiers=tuple(Cashier(f'c{i}',0,end) for i in range(5)))
    return replace(c,**changes).validate()


def client(id,arrival=0,products=10,**changes):
    return Customer(str(id),arrival,products,**changes)
