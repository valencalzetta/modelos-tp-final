"""Flujos independientes por mecanismo; no dependen de las decisiones de servicio."""
import hashlib
import random
from .domain import Customer


def stable_seed(seed, *keys):
    content = repr((seed, *keys)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(content).digest()[:16], "big")


def payment_draw(seed, day, customer_id, attempt):
    return random.Random(stable_seed(seed, "rechazo", day, customer_id, attempt)).random()


def generate_day(config, seed, day):
    config.validate()
    if not 0 <= day < config.days:
        raise ValueError("Día fuera del horizonte")
    customers = []
    promotion = day == config.promotion_day
    for band in config.bands:
        arrivals = random.Random(stable_seed(seed, day, band.name, "llegadas"))
        baskets = random.Random(stable_seed(seed, day, band.name, "canastas"))
        payments = random.Random(stable_seed(seed, day, band.name, "pagos"))
        priorities = random.Random(stable_seed(seed, day, band.name, "prioridad"))
        rate = band.rate * config.demand_multiplier
        if promotion:
            rate *= config.promotion_multiplier
        if rate == 0:
            continue
        time = band.start
        index = 0
        while True:
            time += arrivals.expovariate(rate)
            if time >= band.end:
                break
            products = baskets.randint(config.products_min, config.products_max)
            if promotion:
                products = max(1, round(products * config.promotion_products_multiplier))
            customers.append(Customer(
                id=f"{day}-{band.name}-{index}", arrival=time, products=products,
                payment="efectivo" if payments.random() < config.cash_fraction else "digital",
                priority=priorities.random() < config.priority_fraction,
                day=day, patience=config.patience_minutes))
            index += 1
    return customers
