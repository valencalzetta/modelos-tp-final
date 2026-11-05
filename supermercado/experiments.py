"""Diseños experimentales, réplicas pareadas y exportaciones reproducibles."""
from dataclasses import replace
import csv
import hashlib
from itertools import product
import json
import platform
from pathlib import Path
from .config import with_capacity, roster_for_bands
from .engine import simulate_week
from .metrics import cohort_rows, resource_rows, week_metrics
from .statistics import mean_interval, wilson_interval, paired_interval
from .validation import verify_day


def write_json(path, data):
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def write_csv(path, rows):
    rows = list(rows)
    with Path(path).open('w',newline='',encoding='utf-8') as stream:
        if rows:
            writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def source_digest():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob('*.py')):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def manifest(configs, seeds, **extra):
    data = {name:c.to_dict() for name,c in configs.items()}
    return dict(python=platform.python_version(),source_sha256=source_digest(),
                config_sha256=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest(),
                seeds=seeds,configs=data,**extra)


def variants(config, plan, adjust_staff=False):
    base = (replace(config,cashiers=roster_for_bands(config.bands),
                    assumptions={**config.assumptions,'cashiers':
                    'Cobertura sintética por franja según la política; sustituye agendas, velocidades, pausas y ausencias originales'})
            if adjust_staff else config)
    result = {}
    if plan == 'comparacion':
        for name,c in [('referencia',base),('cinco_todas_franjas',with_capacity(base,[5]*len(base.bands),adjust_staff))]:
            for mode in ('normal','rapida_exclusiva','rapida_flexible'):
                result[f'{name}_{mode}'] = replace(c,mode=mode).validate()
    elif plan == 'filas':
        # Cada par sólo cambia la organización de filas. Sin cambios voluntarios;
        # se conserva la redistribución obligatoria cuando una caja cierra.
        for name,c in variants(config,'comparacion',adjust_staff).items():
            for queue in ('unica','individuales'):
                result[f'{name}_{queue}'] = replace(c,queue_mode=queue,switch_threshold=None,
                    assumptions={**c.assumptions,'comparacion_filas':
                        'Fila única frente a menor fila individual incluyendo ocupado; desempate por caja; sin cambios voluntarios'}).validate()
    elif plan == 'capacidad':
        for counts in product(range(1,6),repeat=len(base.bands)):
            result['cajas_'+'_'.join(map(str,counts))] = replace(with_capacity(base,counts,adjust_staff),mode='normal')
    elif plan == 'factorial':
        # Cada franja tiene niveles explícitos, siempre dentro de las cinco cajas.
        policies = ([3]*len(base.bands),[4]*len(base.bands),[5]*len(base.bands))
        for counts,multiplier,mode in product(policies,(1.2,1.4,1.6),('normal','rapida_exclusiva','rapida_flexible')):
            c = with_capacity(base,counts,adjust_staff)
            result[f'cajas{counts[0]}_promo{multiplier}_{mode}'] = replace(c,mode=mode,promotion_multiplier=multiplier).validate()
    elif plan == 'sensibilidad':
        result['referencia'] = base
        factors = [('demanda_baja','demand_multiplier',base.demand_multiplier*.8),
                   ('demanda_alta','demand_multiplier',base.demand_multiplier*1.2),
                   ('escaneo_010','scan_minutes',.10),('escaneo_020','scan_minutes',.20),
                   ('efectivo_010','cash_fraction',.10),('efectivo_050','cash_fraction',.50),
                   ('promo_020','promotion_multiplier',1.2),('promo_060','promotion_multiplier',1.6)]
        for name,key,value in factors:
            result[name] = replace(base,**{key:value}).validate()
        for limit in (5,10,15):
            result[f'limite_rapida_{limit}'] = replace(base,mode='rapida_exclusiva',quick_limit=limit).validate()
        result['demanda_alta_escaneo_lento'] = replace(base,demand_multiplier=base.demand_multiplier*1.2,scan_minutes=.2)
    elif plan == 'estres':
        result['referencia'] = base
        result['doble_demanda'] = replace(base,demand_multiplier=base.demand_multiplier*2)
        day = base.promotion_day
        morning = base.bands[0]
        candidates = [w for w in base.cashiers if day in w.days and w.start <= morning.start < w.end]
        if not candidates:
            raise ValueError('El estrés requiere un cajero presente en la mañana de promoción')
        first = candidates[0].id
        cashiers = tuple(replace(w,absences=w.absences+((day,morning.start,morning.end),))
                         if w.id == first else w for w in base.cashiers)
        result['ausencia_manana_promocion'] = replace(base,cashiers=cashiers)
        result['adverso_combinado'] = replace(base,cashiers=cashiers,promotion_multiplier=1.6,cash_fraction=.5)
    else:
        raise ValueError('Plan experimental desconocido')
    return {name:c.validate() for name,c in result.items()}


def run_once(config, seed, output, trace=True):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    week = simulate_week(config,seed,trace)
    errors = [dict(day=d.day,error=e) for d in week.days for e in verify_day(d,config)]
    summary = week_metrics(week,config)
    write_json(output/'manifest.json',manifest({'corrida':config},[seed]))
    write_json(output/'resumen.json',summary)
    write_json(output/'verificacion.json',dict(ok=not errors,errors=errors,
               alcance='Invariantes y contabilidad del programa; no validación empírica'))
    write_csv(output/'clientes.csv',[r.to_dict() for d in week.days for r in d.records])
    write_csv(output/'cohortes.csv',[r for d in week.days for r in cohort_rows(d,config)])
    write_csv(output/'recursos.csv',[r for d in week.days for r in resource_rows(d)])
    write_csv(output/'dias.csv',[dict(dia=d.day,estado=d.status,fin=d.finish,
              pendientes_al_cierre=d.pending_at_close,motivo=d.note) for d in week.days])
    if trace:
        write_csv(output/'eventos.csv',[dict(dia=d.day,time=e['time'],kind=e['kind'],
                  detalle=json.dumps({k:v for k,v in e.items() if k not in ('time','kind')},ensure_ascii=False))
                  for d in week.days for e in d.events])
        write_csv(output/'intervalos.csv',[dict(dia=d.day,**i) for d in week.days for i in d.intervals])
    if errors:
        raise RuntimeError(f'Falló la verificación: {errors[:3]}')
    return summary


def run_experiment(config, plan, replicas, seed, output, confidence=.9,
                   target_success=None, adjust_staff=False, progress=None):
    if type(replicas) is not int or replicas < 2:
        raise ValueError('Se requieren al menos dos réplicas para inferencia entre semanas')
    if not 0 < confidence < 1:
        raise ValueError('Confianza fuera de (0,1)')
    if target_success is not None and not 0 < target_success <= 1:
        raise ValueError('Meta de cumplimiento fuera de (0,1]')
    configs = variants(config,plan,adjust_staff)
    seeds = list(range(seed,seed+replicas))
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    write_json(output/'manifest.json',manifest(configs,seeds,plan=plan,confidence=confidence,
                target_success=target_success,adjust_staff=adjust_staff,
                precision='Tamaño fijo; piloto no garantiza una precisión específica'))
    rows,cohorts = [],[]
    for name,c in configs.items():
        for s in seeds:
            week = simulate_week(c,s,trace=False)
            errors = [e for d in week.days for e in verify_day(d,c)]
            if errors:
                raise RuntimeError(f'{name}, semilla {s}: {errors[:3]}')
            rows.append(dict(escenario=name,**week_metrics(week,c)))
            cohorts.extend(dict(escenario=name,semilla=s,**r) for d in week.days for r in cohort_rows(d,c))
        if progress:
            progress(name,len(rows),len(configs)*replicas)
    summaries = {}
    for name in configs:
        group = [r for r in rows if r['escenario'] == name]
        statistics = {}
        for metric in ('max_p95_franja','espera_media','horas_caja','horas_cajero','horas_cajero_extra','costo_personal'):
            statistics[metric] = mean_interval([r[metric] for r in group
                                                if r['estado'] == 'completo' and r[metric] is not None],confidence)
        valid = [r for r in group if r['cumple_servicio_semana'] is not None]
        statistics['cumplimiento_semanal'] = wilson_interval(sum(r['cumple_servicio_semana'] is True for r in valid),len(valid),confidence)
        statistics['semanas_inviables'] = sum(r['estado'] != 'completo' for r in group)
        statistics['alcance_intervalos_medias'] = ('Condicional a semanas operativamente completas; no estima semanas inviables'
                                                  if statistics['semanas_inviables'] else 'Semanas completas del escenario')
        summaries[name] = statistics
    reference = next(iter(configs))
    pairs = {}
    for name in configs:
        if plan == 'filas':
            reference = name.rsplit('_',1)[0] + '_unica'
        base = {r['semilla']:r['max_p95_franja'] for r in rows if r['escenario'] == reference}
        other = {r['semilla']:r['max_p95_franja'] for r in rows if r['escenario'] == name}
        valid_seeds = {s for s in seeds if base[s] is not None and other[s] is not None}
        pairs[name] = dict(reference=reference,metric='max_p95_franja',
                           difference='alternativa menos referencia; negativo indica menor espera',
                           excluded_seeds=sorted(set(seeds)-valid_seeds),
                           **paired_interval({s:base[s] for s in valid_seeds},{s:other[s] for s in valid_seeds},confidence))
    recommendation = dict(target_success=target_success,eligible=[],selected=None,
                          inference_scope='Exploratorio: intervalos por alternativa, sin ajuste por selección múltiple; confirmar finalistas con nuevas réplicas',
                          criterion='Límite inferior Wilson >= meta, sin semanas inviables; después menor hora de cajero y de caja')
    if target_success is None:
        recommendation['reason'] = 'Falta acordar una meta probabilística; se presentan comparaciones sin declarar ganadora'
    else:
        eligible = [name for name,s in summaries.items()
                    if s['cumplimiento_semanal']['n'] == replicas and s['semanas_inviables'] == 0
                    and s['cumplimiento_semanal']['lower'] >= target_success]
        recommendation['eligible'] = eligible
        if eligible:
            recommendation['selected'] = min(eligible,key=lambda n:(summaries[n]['horas_cajero']['mean'],summaries[n]['horas_caja']['mean']))
            recommendation['reason'] = 'Selección condicional a los supuestos y escenarios ensayados; requiere validación empírica'
        else:
            recommendation['reason'] = 'Ninguna alternativa demuestra la meta con esta muestra y este criterio'
    write_csv(output/'replicas.csv',rows)
    write_csv(output/'cohortes.csv',cohorts)
    write_json(output/'estadisticas.json',summaries)
    write_json(output/'comparaciones_pareadas.json',pairs)
    write_json(output/'recomendacion.json',recommendation)
    return summaries,recommendation
