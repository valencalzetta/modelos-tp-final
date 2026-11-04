"""Verificación independiente de trazas, conservación y áreas temporales."""
import math


def verify_day(result, config):
    errors = []
    def equal(a,b):
        return math.isclose(a,b,rel_tol=1e-9,abs_tol=1e-7)
    ids = [r.customer.id for r in result.records]
    if len(ids) != len(set(ids)):
        errors.append('Identificadores de clientes duplicados')
    by_box, by_worker = {}, {}
    queue_area = busy_area = 0.0
    for r in result.records:
        end_wait = r.start if r.start is not None else (r.exit_time if r.exit_time is not None else result.finish)
        queue_area += end_wait-r.customer.arrival
        if r.start is not None:
            finish = r.finish if r.finish is not None else result.finish
            busy_area += finish-r.start
            if not r.customer.arrival <= r.start <= finish:
                errors.append(f'{r.customer.id}: orden temporal inválido')
            if r.box not in range(1,6) or r.cashier not in result.cashier_minutes:
                errors.append(f'{r.customer.id}: recurso inexistente')
            if r.finish is not None and not equal(r.finish-r.start,r.scan+r.payment_time+r.retry_time):
                errors.append(f'{r.customer.id}: duración no coincide con actividades')
            if (config.mode == 'rapida_exclusiva' and r.box == 1
                    and r.customer.products > config.quick_limit):
                errors.append(f'{r.customer.id}: compra no elegible en rápida exclusiva')
            by_box.setdefault(r.box,[]).append((r.start,finish))
            by_worker.setdefault(r.cashier,[]).append((r.start,finish))
        if r.status in ('atendido','pago_fallido') and (r.start is None or r.finish is None):
            errors.append(f'{r.customer.id}: finalización sin atención')
        if r.status == 'abandono' and (r.start is not None or r.exit_time is None):
            errors.append(f'{r.customer.id}: abandono inconsistente')
        if r.status in ('pendiente','atendiendo') and result.status == 'completo':
            errors.append('Resultado completo con clientes pendientes')
    for category, resources in (('caja',by_box),('cajero',by_worker)):
        for key, intervals in resources.items():
            intervals.sort()
            for first,second in zip(intervals,intervals[1:]):
                if second[0] < first[1]-1e-8:
                    errors.append(f'Superposición por {category} {key}')
    resources = list(result.resources.values())
    if not equal(queue_area,sum(r['queue_area'] for r in resources)):
        errors.append('Área de cola no coincide con esperas acumuladas')
    if not equal(busy_area,sum(r['busy_minutes'] for r in resources)):
        errors.append('Área ocupada no coincide con servicios')
    if not equal(sum(result.cashier_minutes.values()),sum(r['staff_minutes'] for r in resources)):
        errors.append('Horas de personal inconsistentes')
    if not equal(sum(result.box_minutes.values()),sum(r['enabled_minutes'] for r in resources)):
        errors.append('Horas de cajas inconsistentes')
    for i in result.intervals:
        if not 0 <= i['busy'] <= i['enabled'] <= min(5,i['staff']):
            errors.append('Capacidad o disponibilidad de personal excedida')
        if i['queue'] < 0 or i['end'] <= i['start']:
            errors.append('Intervalo de estado inválido')
    return errors
