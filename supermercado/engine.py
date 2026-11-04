"""Motor propio de eventos discretos; sin dependencias externas.

El cierre deja de admitir clientes, pero conserva los cajeros asignados al
cierre para vaciar las filas. Las pausas y salidas de turno no interrumpen
servicios. El límite de continuidad es la apertura del día siguiente.
"""
from dataclasses import dataclass
import heapq
import math
from .domain import Customer, Record, DayResult, WeekResult
from .randomness import generate_day, payment_draw


@dataclass
class _Worker:
    spec: object
    break_until: float = -1
    pending_break: float = 0


@dataclass
class _Box:
    id: int
    worker: str | None = None
    job: str | None = None
    accepting: bool = False


class Simulator:
    def __init__(self, config, customers, day=0, seed=2026, trace=True):
        self.config = config.validate()
        if type(day) is not int or not 0 <= day < config.days:
            raise ValueError("Día fuera del horizonte")
        self.day, self.seed, self.trace = day, seed, trace
        customers = list(customers)
        ids = set()
        for c in customers:
            c.validate(config.close)
            if c.day != day or c.id in ids:
                raise ValueError("Clientes duplicados o correspondientes a otro día")
            ids.add(c.id)
        ordered = sorted(enumerate(customers), key=lambda pair: (pair[1].arrival, pair[0]))
        self.order = {c.id: i for i, (_, c) in enumerate(ordered)}
        self.records = {c.id: Record(c, config.band_at(c.arrival).name) for _, c in ordered}
        self.waiting = {}
        self.workers = {c.id: _Worker(c) for c in config.cashiers if day in c.days}
        self.boxes = [_Box(i) for i in range(1, 6)]
        self.heap, self.sequence = [], 0
        self.events, self.intervals = [], []
        self.time = 0.0
        self.closed = False
        self.retained = set()
        self.pending_at_close = 0
        self.openings = 0
        self.extra = 0
        self.reaction_pending = False
        self.hold_until = 0
        self.close_check = False
        self.resources = {b.name: self._empty_resources() for b in config.bands}
        self.resources["fuera_horario"] = self._empty_resources()
        self.cashier_minutes = {key: 0.0 for key in self.workers}
        self.box_minutes = {b.id: 0.0 for b in self.boxes}
        for _, c in ordered:
            self._push(c.arrival, 30, "llegada", c.id)
        for b in config.bands:
            self._push(b.start, 20, "franja", b.name)
        for key, w in self.workers.items():
            self._push(w.spec.start, 20, "inicio_turno", key)
            self._push(w.spec.end, 20, "fin_turno", key)
            for start, duration in w.spec.breaks:
                self._push(start, 20, "solicitud_pausa", (key, duration))
            for d, start, end in w.spec.absences:
                if d == day:
                    self._push(start, 20, "inicio_ausencia", key)
                    self._push(end, 20, "fin_ausencia", key)
        self._push(config.close, 15, "cierre", None)

    @staticmethod
    def _empty_resources():
        return dict(duration=0.0, queue_area=0.0, priority_queue_area=0.0,
                    busy_minutes=0.0, enabled_minutes=0.0, staff_minutes=0.0, overtime_minutes=0.0,
                    max_queue=0, completions=0, failed_payments=0, abandonments=0)

    def _push(self, time, priority, kind, data):
        if not math.isfinite(time) or time < self.time:
            raise ValueError("Evento en el pasado o tiempo no finito")
        self.sequence += 1
        heapq.heappush(self.heap, (float(time), priority, self.sequence, kind, data))

    def _log(self, kind, **fields):
        if self.trace:
            self.events.append(dict(time=self.time, kind=kind, **fields))

    def _busy(self, worker):
        return any(b.job is not None and b.worker == worker for b in self.boxes)

    def _absent(self, worker):
        return any(d == self.day and start <= self.time < end
                   for d, start, end in worker.spec.absences)

    def _scheduled(self, key):
        w = self.workers[key]
        return (w.spec.start <= self.time < w.spec.end
                or (self.closed and key in self.retained and w.spec.end >= self.config.close))

    def _present(self, key):
        return (self._scheduled(key) and not self._absent(self.workers[key])) or self._busy(key)

    def _available(self, key):
        w = self.workers[key]
        return (self._scheduled(key) and not self._absent(w)
                and self.time >= w.break_until and not w.pending_break)

    def _requested(self):
        band = self.config.band_at(self.time) or self.config.bands[-1]
        return min(5, band.boxes + self.extra)

    def _reconcile(self):
        desired = self._requested()
        for b in self.boxes:
            old = b.accepting
            if b.job is None and (b.id > desired or b.worker is None or not self._available(b.worker)):
                b.worker = None
            b.accepting = b.id <= desired and b.worker is not None and self._available(b.worker)
            if old and not b.accepting:
                self._log("caja_pendiente_cierre" if b.job else "caja_cerrada", box=b.id)
        used = {b.worker for b in self.boxes if b.worker is not None}
        free = sorted(key for key in self.workers if key not in used and self._available(key))
        for b in self.boxes:
            if b.id <= desired and b.worker is None and free:
                b.worker = free.pop(0)
                b.accepting = True
                self.openings += 1
                self._log("caja_abierta", box=b.id, cashier=b.worker)

    def _quick(self, b):
        return b.id == 1 and self.config.mode != "normal"

    def _eligible(self, record, b):
        return not (self._quick(b) and self.config.mode == "rapida_exclusiva"
                    and record.customer.products > self.config.quick_limit)

    def _queue_options(self, r):
        boxes = [b for b in self.boxes if b.accepting and self._eligible(r, b)]
        # En individuales, las compras grandes eligen normales; la rápida flexible
        # puede tomarlas de esas filas al quedar sin compras pequeñas.
        if self.config.mode == "rapida_flexible" and r.customer.products > self.config.quick_limit:
            normals = [b for b in boxes if not self._quick(b)]
            boxes = normals or boxes
        return boxes

    def _queue_size(self, box):
        return sum(r.queue == box.id for r in self.waiting.values()) + int(box.job is not None)

    def _choose_queue(self, r):
        options = self._queue_options(r)
        return min(options, key=lambda b: (self._queue_size(b), b.id)).id if options else None

    def _route(self):
        if self.config.queue_mode == "unica":
            return
        accepting = {b.id for b in self.boxes if b.accepting}
        for r in sorted(self.waiting.values(), key=self._rank):
            old = r.queue
            if old not in accepting:
                new = self._choose_queue(r)
            elif self.config.switch_threshold is not None:
                new = self._choose_queue(r)
                if new is not None:
                    old_box = self.boxes[old - 1]
                    if self._queue_size(old_box) - self._queue_size(self.boxes[new - 1]) < self.config.switch_threshold:
                        new = old
            else:
                new = old
            if new != old:
                r.queue = new
                if old is not None:
                    r.queue_changes += 1
                    self._log("cambio_fila", id=r.customer.id, previous=old, queue=new)

    def _rank(self, r):
        return (not r.customer.priority, r.customer.arrival, self.order[r.customer.id])

    def _select(self, box):
        candidates = [r for r in self.waiting.values() if self._eligible(r, box)]
        if self.config.queue_mode == "individuales":
            candidates = [r for r in candidates if r.queue == box.id]
        if self._quick(box):
            small = [r for r in candidates if r.customer.products <= self.config.quick_limit]
            if small:
                candidates = small
            elif self.config.mode == "rapida_flexible":
                candidates = list(self.waiting.values())
        return min(candidates, key=self._rank) if candidates else None

    def _dispatch(self):
        self._reconcile()
        self._route()
        for b in self.boxes:  # La rápida es caja 1; se asigna primero.
            if b.job is not None or not b.accepting:
                continue
            r = self._select(b)
            if r is None:
                continue
            del self.waiting[r.customer.id]
            if self.config.queue_mode == "individuales" and r.queue != b.id:
                r.queue_changes += 1
            r.queue = b.id if self.config.queue_mode == "individuales" else None
            r.start, r.box, r.cashier = self.time, b.id, b.worker
            r.status = "atendiendo"
            r.flexible_exception = (self._quick(b) and r.customer.products > self.config.quick_limit)
            r.scan = self.config.scan_minutes * r.customer.products * self.workers[b.worker].spec.speed
            b.job = r.customer.id
            self._log("inicio_atencion", id=b.job, box=b.id, cashier=b.worker)
            self._push(self.time + r.scan, 10, "fin_escaneo", b.job)

    def _start_break(self, key, duration):
        w = self.workers[key]
        w.pending_break = 0
        w.break_until = max(self.time, w.break_until) + duration
        self._log("inicio_pausa", cashier=key, until=w.break_until)
        self._push(w.break_until, 20, "fin_pausa", (key, w.break_until))

    def _start_payment(self, r, fallback=False):
        r.attempts += 1
        cash = fallback or r.customer.payment == "efectivo"
        duration = self.config.cash_payment_minutes if cash else self.config.digital_payment_minutes
        r.payment_time += duration
        self._log("inicio_pago", id=r.customer.id, attempt=r.attempts, cash=cash)
        self._push(self.time + duration, 10, "fin_pago", (r.customer.id, cash))

    def _finish(self, r, success):
        r.finish = r.exit_time = self.time
        r.status = "atendido" if success else "pago_fallido"
        b = self.boxes[r.box - 1]
        b.job = None
        bucket = self.config.band_at(self.time)
        resources = self.resources[bucket.name if bucket else "fuera_horario"]
        resources["completions" if success else "failed_payments"] += 1
        self._log("fin_atencion", id=r.customer.id, box=b.id, cashier=b.worker, success=success)
        w = self.workers[b.worker]
        if w.pending_break:
            self._start_break(b.worker, w.pending_break)

    def _handle(self, kind, data):
        if kind == "llegada":
            r = self.records[data]
            self.waiting[data] = r
            self._log(kind, id=data)
            if r.customer.patience is not None:
                self._push(self.time + r.customer.patience, 40, "abandono", data)
        elif kind == "fin_escaneo":
            self._log(kind, id=data)
            self._start_payment(self.records[data])
        elif kind == "reintento":
            self._start_payment(self.records[data])
        elif kind == "respaldo_efectivo":
            self._start_payment(self.records[data], fallback=True)
        elif kind == "fin_pago":
            key, cash = data
            r = self.records[key]
            draw = (r.customer.payment_draws[r.attempts - 1]
                    if r.attempts <= len(r.customer.payment_draws)
                    else payment_draw(self.seed, self.day, key, r.attempts))
            rejected = not cash and draw < self.config.rejection_probability
            self._log("resultado_pago", id=key, rejected=rejected)
            if not rejected:
                self._finish(r, True)
            else:
                r.rejections += 1
                if r.attempts < self.config.max_payment_attempts:
                    r.retry_time += self.config.retry_delay
                    self._push(self.time + self.config.retry_delay, 10, "reintento", key)
                elif self.config.payment_exhaustion == "efectivo":
                    r.fallback_cash = True
                    self._push(self.time, 10, "respaldo_efectivo", key)
                else:
                    self._finish(r, False)
        elif kind == "cierre":
            self.closed = True
            self.retained = {b.worker for b in self.boxes if b.worker is not None}
            self.pending_at_close = len(self.waiting) + sum(b.job is not None for b in self.boxes)
            self._log(kind, pending=self.pending_at_close)
        elif kind == "solicitud_pausa":
            key, duration = data
            if self._busy(key):
                self.workers[key].pending_break += duration
                self._log("pausa_diferida", cashier=key, duration=duration)
            else:
                self._start_break(key, duration)
        elif kind == "fin_pausa":
            key, until = data
            if until == self.workers[key].break_until:
                self._log(kind, cashier=key)
        elif kind == "apertura_reactiva":
            self.reaction_pending = False
            if len(self.waiting) >= self.config.reactive_threshold:
                self.extra = self.config.reactive_extra_boxes
                self.hold_until = self.time + self.config.reactive_min_open
                self._log(kind, extra=self.extra)
        elif kind == "revisar_reactiva":
            self.close_check = False
        else:
            self._log(kind, data=data)

    def _react(self):
        if self.config.reactive_threshold is None or self.closed:
            return
        if len(self.waiting) >= self.config.reactive_threshold:
            if not self.extra and not self.reaction_pending and self._requested() < 5:
                self.reaction_pending = True
                self._push(self.time + self.config.reactive_delay, 20, "apertura_reactiva", None)
        elif self.extra:
            if self.time >= self.hold_until:
                self.extra = 0
                self._log("cierre_reactivo")
                self._reconcile()
            elif not self.close_check:
                self.close_check = True
                self._push(self.hold_until, 20, "revisar_reactiva", None)

    def _integrate(self, end):
        if end <= self.time:
            return
        cuts = sorted({self.time, end, *(b.end for b in self.config.bands if self.time < b.end < end)})
        queue = len(self.waiting)
        priority_queue = sum(r.customer.priority for r in self.waiting.values())
        busy = sum(b.job is not None for b in self.boxes)
        enabled = [b for b in self.boxes if b.accepting or b.job is not None]
        present = [key for key in self.workers if self._present(key)]
        overtime = sum(self.time >= self.workers[key].spec.end for key in present)
        for left, right in zip(cuts, cuts[1:]):
            duration = right - left
            band = self.config.band_at(left)
            r = self.resources[band.name if band else "fuera_horario"]
            r["duration"] += duration
            r["queue_area"] += queue * duration
            r["priority_queue_area"] += priority_queue * duration
            r["busy_minutes"] += busy * duration
            r["enabled_minutes"] += len(enabled) * duration
            r["staff_minutes"] += len(present) * duration
            r["overtime_minutes"] += overtime * duration
            r["max_queue"] = max(r["max_queue"], queue)
            if self.trace:
                self.intervals.append(dict(start=left, end=right, queue=queue, busy=busy,
                                           enabled=len(enabled), staff=len(present)))
            for b in enabled:
                self.box_minutes[b.id] += duration
            for key in present:
                self.cashier_minutes[key] += duration

    def run(self):
        reason = ""
        while self.heap:
            time = self.heap[0][0]
            active = bool(self.waiting) or any(b.job is not None for b in self.boxes)
            if self.closed and not active:
                break
            if time >= 1440:
                self._integrate(1440)
                self.time = 1440
                reason = "La operación invade la apertura siguiente; no se reinicia la fila"
                break
            self._integrate(time)
            self.time = time
            abandonments = []
            while self.heap and self.heap[0][0] == time:
                _, _, _, kind, data = heapq.heappop(self.heap)
                if kind == "abandono":
                    abandonments.append(data)
                else:
                    self._handle(kind, data)
            self._dispatch()
            # En empate de fin de servicio y paciencia, se permite iniciar atención.
            for key in abandonments:
                if key in self.waiting:
                    r = self.waiting.pop(key)
                    r.status, r.exit_time = "abandono", self.time
                    band = self.config.band_at(self.time)
                    self.resources[band.name if band else "fuera_horario"]["abandonments"] += 1
                    self._log("abandono", id=key)
            self._react()
        pending = [r for r in self.records.values() if r.status in ("pendiente", "atendiendo")]
        status = "completo" if not pending else "inviable"
        if pending and not reason:
            reason = "Clientes pendientes sin capacidad elegible o personal futuro disponible"
        return DayResult(self.day, list(self.records.values()), self.events, self.intervals,
                         self.resources, self.time, status, self.pending_at_close,
                         self.openings, self.cashier_minutes, self.box_minutes, reason)


def simulate_day(config, customers, day=0, seed=2026, trace=True):
    return Simulator(config, customers, day, seed, trace).run()


def simulate_week(config, seed=2026, trace=False, inputs=None):
    config.validate()
    if type(seed) is not int:
        raise ValueError("La semilla debe ser entera")
    if inputs is not None and set(inputs) != set(range(config.days)):
        raise ValueError("Las entradas deben contener exactamente los días del horizonte")
    days = []
    for day in range(config.days):
        customers = generate_day(config, seed, day) if inputs is None else inputs[day]
        result = simulate_day(config, customers, day, seed, trace)
        days.append(result)
        if result.status != "completo":
            return WeekResult(days, seed, "inviable")
    return WeekResult(days, seed, "completo")
