from dataclasses import dataclass, field
import math


@dataclass(frozen=True)
class Customer:
    id: str
    arrival: float
    products: int
    payment: str = "digital"
    priority: bool = False
    day: int = 0
    patience: float | None = None
    payment_draws: tuple[float, ...] = ()  # Permite casos manuales sin azar.

    def validate(self, close):
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("Cliente sin identificador")
        if (isinstance(self.arrival, bool) or not isinstance(self.arrival, (int, float))
                or not math.isfinite(self.arrival) or not 0 <= self.arrival < close):
            raise ValueError("Llegada fuera del horario")
        if type(self.products) is not int or self.products < 1:
            raise ValueError("Cantidad de productos inválida")
        if self.payment not in ("digital", "efectivo") or type(self.priority) is not bool:
            raise ValueError("Pago o prioridad inválidos")
        if type(self.day) is not int or not 0 <= self.day < 7:
            raise ValueError("Día inválido")
        if self.patience is not None and (isinstance(self.patience, bool)
                or not isinstance(self.patience, (int, float))
                or not math.isfinite(self.patience) or self.patience < 0):
            raise ValueError("Paciencia inválida")
        if any(isinstance(x, bool) or not isinstance(x, (int, float))
               or not math.isfinite(x) or not 0 <= x < 1 for x in self.payment_draws):
            raise ValueError("Sorteos de pago fuera de [0,1)")


@dataclass
class Record:
    customer: Customer
    band: str
    status: str = "pendiente"
    queue: int | None = None
    queue_changes: int = 0
    start: float | None = None
    finish: float | None = None
    exit_time: float | None = None
    box: int | None = None
    cashier: str | None = None
    scan: float = 0.0
    payment_time: float = 0.0
    retry_time: float = 0.0
    attempts: int = 0
    rejections: int = 0
    fallback_cash: bool = False
    flexible_exception: bool = False

    @property
    def wait(self):
        return None if self.start is None else self.start - self.customer.arrival

    @property
    def total(self):
        return None if self.finish is None else self.finish - self.customer.arrival

    def to_dict(self):
        return {"id": self.customer.id, "dia": self.customer.day,
                "franja": self.band, "llegada": self.customer.arrival,
                "productos": self.customer.products, "pago": self.customer.payment,
                "prioritario": self.customer.priority, "estado": self.status,
                "fila": self.queue, "cambios_fila": self.queue_changes,
                "inicio": self.start, "fin": self.finish, "salida": self.exit_time,
                "caja": self.box, "cajero": self.cashier, "espera": self.wait,
                "tiempo_total": self.total, "escaneo": self.scan,
                "tiempo_pago": self.payment_time, "demora_reintentos": self.retry_time,
                "intentos": self.attempts, "rechazos": self.rejections,
                "efectivo_respaldo": self.fallback_cash,
                "excepcion_rapida_flexible": self.flexible_exception}


@dataclass
class DayResult:
    day: int
    records: list[Record]
    events: list[dict]
    intervals: list[dict]
    resources: dict[str, dict[str, float]]
    finish: float
    status: str
    pending_at_close: int
    openings: int
    cashier_minutes: dict[str, float] = field(default_factory=dict)
    box_minutes: dict[int, float] = field(default_factory=dict)
    note: str = ""


@dataclass
class WeekResult:
    days: list[DayResult]
    seed: int
    status: str
