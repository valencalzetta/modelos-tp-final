"""Métricas por cohorte de llegada y contabilidad temporal de recursos."""
from .statistics import percentile


def cohort_rows(day_result, config, groups=True):
    rows = []
    filters = {"todos": lambda r: True}
    if groups:
        filters.update(prioritarios=lambda r: r.customer.priority,
                       normales=lambda r: not r.customer.priority,
                       pequenas=lambda r: r.customer.products <= config.quick_limit,
                       grandes=lambda r: r.customer.products > config.quick_limit)
    for band in config.bands:
        for name, predicate in filters.items():
            records = [r for r in day_result.records if r.band == band.name and predicate(r)]
            started = [r for r in records if r.start is not None]
            waits = [r.wait for r in started]
            totals = [r.total for r in records if r.finish is not None]
            row = dict(dia=day_result.day,franja=band.name,grupo=name,llegados=len(records),
                       atendidos=sum(r.status == "atendido" for r in records),
                       abandonos=sum(r.status == "abandono" for r in records),
                       pagos_fallidos=sum(r.status == "pago_fallido" for r in records),
                       pendientes=sum(r.status in ("pendiente","atendiendo") for r in records),
                       espera_media=sum(waits)/len(waits) if waits else None,
                       espera_maxima=max(waits,default=None),
                       p50_espera=percentile(waits,50), p90_espera=percentile(waits,90),
                       p95_espera=percentile(waits,95), p99_espera=percentile(waits,99),
                       p95_total=percentile(totals,95),
                       fraccion_espera_ge_sla=sum(w >= config.sla_minutes for w in waits)/len(waits) if waits else None)
            row['cumple_espera'] = row['p95_espera'] < config.sla_minutes if waits else None
            # Las celdas sin observaciones no prueban cumplimiento.
            row['cumple_servicio'] = (row['cumple_espera'] and not row['abandonos']
                                       and not row['pagos_fallidos'] and not row['pendientes']) if records else None
            rows.append(row)
    return rows


def resource_rows(day_result):
    rows = []
    for band, r in day_result.resources.items():
        rows.append(dict(dia=day_result.day,franja=band,**r,
                         cola_media=r['queue_area']/r['duration'] if r['duration'] else None,
                         utilizacion=r['busy_minutes']/r['enabled_minutes'] if r['enabled_minutes'] else None,
                         throughput_hora=r['completions']*60/r['duration'] if r['duration'] else None))
    return rows


def week_metrics(week, config):
    cohorts = [r for d in week.days for r in cohort_rows(d,config,groups=False)]
    observed = [r for r in cohorts if r['llegados']]
    records = [r for d in week.days for r in d.records]
    waits = [r.wait for r in records if r.start is not None]
    area = sum(r['queue_area'] for d in week.days for r in d.resources.values())
    busy = sum(r['busy_minutes'] for d in week.days for r in d.resources.values())
    enabled = sum(r['enabled_minutes'] for d in week.days for r in d.resources.values())
    staff = sum(r['staff_minutes'] for d in week.days for r in d.resources.values())
    overtime = sum(r['overtime_minutes'] for d in week.days for r in d.resources.values())
    after_close = sum(d.resources['fuera_horario']['staff_minutes'] for d in week.days)
    complete = week.status == 'completo' and len(week.days) == config.days
    observed_max = max((r['p95_espera'] for r in observed if r['p95_espera'] is not None),default=None)
    observed_mean = sum(waits)/len(waits) if waits else None
    success = (week.status == 'completo' and len(week.days) == config.days
               and all(r['cumple_servicio'] is True for r in observed)) if observed else None
    waiting_success = (week.status == 'completo' and len(week.days) == config.days
                       and all(r['cumple_espera'] is True for r in observed)) if observed else None
    return dict(semilla=week.seed,estado=week.status,dias_simulados=len(week.days),
                llegados=len(records),atendidos=sum(r.status == 'atendido' for r in records),
                abandonos=sum(r.status == 'abandono' for r in records),
                pagos_fallidos=sum(r.status == 'pago_fallido' for r in records),
                pendientes=sum(r.status in ('pendiente','atendiendo') for r in records),
                espera_media=observed_mean if complete else None,
                espera_media_observada=observed_mean,
                p95_espera_global=percentile(waits,95) if complete else None,
                max_p95_franja=observed_max if complete else None,
                max_p95_observado=observed_max,
                cumple_espera_semana=waiting_success,cumple_servicio_semana=success,
                horas_caja=enabled/60,horas_cajero=staff/60,horas_cajero_extra=overtime/60,horas_cajero_post_cierre=after_close/60,
                costo_personal=(staff-overtime+overtime*config.overtime_wage_multiplier)*config.hourly_wage/60
                    if config.hourly_wage is not None else None,
                utilizacion=busy/enabled if enabled else None,area_cola=area,
                pendientes_al_cierre=sum(d.pending_at_close for d in week.days),
                max_minutos_extra=max((max(0,d.finish-config.close) for d in week.days),default=0),
                aperturas=sum(d.openings for d in week.days))


def recovery_time(day, after, queue_threshold=0, sustain=10.0):
    """Primer instante tras la perturbación con cola <= umbral durante sustain.

    Necesita traza temporal. Devuelve None si no se observa recuperación completa.
    No supone que un salto instantáneo o fin de observación pruebe estabilidad.
    """
    if after < 0 or queue_threshold < 0 or sustain <= 0:
        raise ValueError('Criterio de recuperación inválido')
    if not day.intervals:
        raise ValueError('La recuperación necesita ejecutar con trace=True')
    start = None
    for interval in day.intervals:
        if interval['end'] <= after:
            continue
        if interval['queue'] <= queue_threshold:
            if start is None:
                start = max(after,interval['start'])
            if interval['end']-start >= sustain:
                return start-after
        else:
            start = None
    return None
