"""Interfaz de línea de comandos: python -m supermercado --help."""
import argparse
from pathlib import Path
import json
import sys
from .config import Config
from .experiments import run_once, run_experiment


def main(argv=None):
    parser = argparse.ArgumentParser(description='Modelo integrador de operación de cajas')
    commands = parser.add_subparsers(dest='command',required=True)
    once = commands.add_parser('simular',help='Simular una semana y exportar trazas')
    experiment = commands.add_parser('experimentar',help='Comparar políticas con réplicas independientes')
    for sub in (once,experiment):
        sub.add_argument('--config',required=True)
        sub.add_argument('--semilla',type=int,default=2026)
        sub.add_argument('--salida',required=True)
        sub.add_argument('--prioritarios',type=float,help='Supuesto explícito que reemplaza priority_fraction')
    once.add_argument('--sin-traza',action='store_true')
    experiment.add_argument('--plan',choices=['comparacion','capacidad','factorial','sensibilidad','estres'],default='comparacion')
    experiment.add_argument('--replicas',type=int,default=30)
    experiment.add_argument('--confianza',type=float,default=.90)
    experiment.add_argument('--meta-cumplimiento',type=float)
    experiment.add_argument('--ajustar-dotacion',action='store_true',
                            help='Generar cobertura sintética por franja según cajas; reemplaza agendas y pausas del archivo')
    args = parser.parse_args(argv)
    try:
        data = json.loads(Path(args.config).read_text(encoding='utf-8'))
        if args.prioritarios is not None:
            data['priority_fraction'] = args.prioritarios
            data['assumptions'] = {**data.get('assumptions',{}),'priority_fraction':'Valor indicado por CLI'}
        config = Config.from_dict(data)
        if args.command == 'simular':
            summary = run_once(config,args.semilla,args.salida,not args.sin_traza)
            print(json.dumps(summary,ensure_ascii=False,indent=2))
        else:
            summaries,recommendation = run_experiment(config,args.plan,args.replicas,args.semilla,args.salida,
                    args.confianza,args.meta_cumplimiento,args.ajustar_dotacion,
                    progress=lambda name,n,total: print(f'{name}: {n}/{total} semanas',flush=True))
            print(json.dumps(recommendation,ensure_ascii=False,indent=2))
        print(f'Resultados: {args.salida}')
        return 0
    except (ValueError,TypeError,OSError,RuntimeError) as error:
        print(f'Error: {error}',file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
