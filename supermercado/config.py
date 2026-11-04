"""Configuraciones explícitas. Todos los tiempos internos son minutos desde las 8."""
from dataclasses import asdict, dataclass, field, replace
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Band:
    name: str
    start: float
    end: float
    rate: float
    boxes: int


@dataclass(frozen=True)
class Cashier:
    id: str
    start: float
    end: float
    days: tuple[int, ...] = tuple(range(7))
    speed: float = 1.0  # Multiplica el tiempo de escaneo, no el de pago.
    breaks: tuple[tuple[float, float], ...] = ()  # (inicio solicitado, duración).
    absences: tuple[tuple[int, float, float], ...] = ()  # (día, inicio, fin).


@dataclass(frozen=True)
class Config:
    bands: tuple[Band, ...] = (
        Band("manana", 0, 300, 1.0, 5),
        Band("tarde", 300, 600, 0.8, 4),
        Band("noche", 600, 840, 0.5, 3),
    )
    installed_boxes: int = 5
    days: int = 7
    promotion_day: int = 2
    promotion_multiplier: float = 1.4
    demand_multiplier: float = 1.0
    products_min: int = 1
    products_max: int = 40
    promotion_products_multiplier: float = 1.0
    cash_fraction: float = 0.3
    priority_fraction: float | None = None  # Obligatorio: no figura en los bloques.
    scan_minutes: float = 0.15
    digital_payment_minutes: float = 1.0
    cash_payment_minutes: float = 2.0
    mode: str = "normal"  # normal, rapida_exclusiva, rapida_flexible.
    queue_mode: str = "unica"  # unica, individuales.
    quick_limit: int = 10
    switch_threshold: int | None = None
    rejection_probability: float = 0.0
    max_payment_attempts: int = 1
    retry_delay: float = 0.0
    payment_exhaustion: str = "fallida"  # fallida o efectivo.
    patience_minutes: float | None = None
    sla_minutes: float = 10.0
    hourly_wage: float | None = None
    overtime_wage_multiplier: float = 1.0
    reactive_threshold: int | None = None
    reactive_extra_boxes: int = 1
    reactive_delay: float = 0.0
    reactive_min_open: float = 0.0
    cashiers: tuple[Cashier, ...] = ()
    assumptions: dict[str, str] = field(default_factory=dict)

    @property
    def close(self):
        return self.bands[-1].end

    def band_at(self, time):
        return next((b for b in self.bands if b.start <= time < b.end), None)

    def validate(self):
        def number(value, name, low=0, strict=False):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or (value <= low if strict else value < low)):
                raise ValueError(f"{name}: número finito {'mayor que' if strict else '>='} {low}")
        def integer(value, name, low, high=None):
            if type(value) is not int or value < low or (high is not None and value > high):
                raise ValueError(f"{name}: entero entre {low} y {high}")
        integer(self.installed_boxes, "installed_boxes", 5, 5)
        integer(self.days, "days", 1, 7)
        integer(self.promotion_day, "promotion_day", 0, 6)
        integer(self.products_min, "products_min", 1)
        integer(self.products_max, "products_max", self.products_min)
        integer(self.quick_limit, "quick_limit", 1)
        integer(self.max_payment_attempts, "max_payment_attempts", 1)
        integer(self.reactive_extra_boxes, "reactive_extra_boxes", 1, 5)
        if not self.bands or self.bands[0].start != 0:
            raise ValueError("Las franjas deben empezar en cero")
        seen = set()
        previous = 0
        for b in self.bands:
            if not b.name or b.name in seen or b.name == "fuera_horario":
                raise ValueError("Nombres de franjas inválidos o duplicados")
            seen.add(b.name)
            number(b.start, "band.start")
            number(b.end, "band.end", b.start, strict=True)
            number(b.rate, "band.rate")
            integer(b.boxes, "band.boxes", 1, 5)
            if b.start != previous:
                raise ValueError("Las franjas deben ser contiguas y sin solapamientos")
            previous = b.end
        if self.close > 840:
            raise ValueError("El horario de admisión no puede superar las 22")
        for name in ("promotion_multiplier", "demand_multiplier", "promotion_products_multiplier",
                     "digital_payment_minutes", "cash_payment_minutes", "sla_minutes",
                     "overtime_wage_multiplier"):
            number(getattr(self, name), name, strict=True)
        for name in ("scan_minutes", "retry_delay", "reactive_delay", "reactive_min_open"):
            number(getattr(self, name), name)
        if self.priority_fraction is None:
            raise ValueError("Definir priority_fraction explícitamente: falta en los bloques")
        for name in ("cash_fraction", "priority_fraction", "rejection_probability"):
            number(getattr(self, name), name)
            if getattr(self, name) > 1:
                raise ValueError(f"{name} debe estar entre cero y uno")
        for name in ("patience_minutes", "hourly_wage"):
            if getattr(self, name) is not None:
                number(getattr(self, name), name)
        for name in ("switch_threshold", "reactive_threshold"):
            if getattr(self, name) is not None:
                integer(getattr(self, name), name, 2 if name == "switch_threshold" else 1)
        if self.switch_threshold is not None and self.queue_mode != "individuales":
            raise ValueError("switch_threshold sólo corresponde a filas individuales")
        if self.mode not in ("normal", "rapida_exclusiva", "rapida_flexible"):
            raise ValueError("Modalidad de caja desconocida")
        if self.queue_mode not in ("unica", "individuales"):
            raise ValueError("Modalidad de fila desconocida")
        if self.payment_exhaustion not in ("fallida", "efectivo"):
            raise ValueError("payment_exhaustion debe ser fallida o efectivo")
        if not self.cashiers:
            raise ValueError("Definir la agenda de cajeros explícitamente")
        ids = set()
        for c in self.cashiers:
            if not c.id or c.id in ids:
                raise ValueError("Los identificadores de cajeros deben ser únicos")
            ids.add(c.id)
            number(c.start, "cashier.start")
            number(c.end, "cashier.end", c.start, strict=True)
            number(c.speed, "cashier.speed", strict=True)
            if c.end > self.close or not c.days or len(c.days) != len(set(c.days)):
                raise ValueError("Agenda fuera del horario o días repetidos")
            for day in c.days:
                integer(day, "cashier.day", 0, 6)
            last_end = c.start
            for start, duration in sorted(c.breaks):
                number(start, "break.start", c.start)
                number(duration, "break.duration", strict=True)
                if start < last_end or start + duration > c.end:
                    raise ValueError("Pausas superpuestas o fuera del turno")
                last_end = start + duration
            for day, start, end in c.absences:
                integer(day, "absence.day", 0, 6)
                number(start, "absence.start")
                number(end, "absence.end", start, strict=True)
        return self

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        data = dict(data)
        if "bands" in data:
            data["bands"] = tuple(Band(**b) for b in data["bands"])
        if "cashiers" in data:
            converted = []
            for c in data["cashiers"]:
                c = dict(c)
                for key in ("days", "breaks", "absences"):
                    if key in c:
                        c[key] = tuple(tuple(v) if isinstance(v, list) else v for v in c[key])
                converted.append(Cashier(**c))
            data["cashiers"] = tuple(converted)
        return cls(**data).validate()

    @classmethod
    def load(cls, path):
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def roster_for_bands(bands):
    """Cobertura sintética por franja, explícita; no resuelve convenios laborales."""
    return tuple(Cashier(f"{b.name}-{i+1}", b.start, b.end)
                 for b in bands for i in range(b.boxes))


def with_capacity(config, counts, adjust_staff=False):
    if len(counts) != len(config.bands):
        raise ValueError("Una cantidad de cajas por franja")
    bands = tuple(replace(b, boxes=n) for b, n in zip(config.bands, counts))
    cashiers = roster_for_bands(bands) if adjust_staff else config.cashiers
    return replace(config, bands=bands, cashiers=cashiers).validate()
