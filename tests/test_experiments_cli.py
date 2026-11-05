from contextlib import redirect_stdout,redirect_stderr
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from supermercado.__main__ import main
from supermercado.config import Config,Band,Cashier
from supermercado.experiments import variants,run_once,run_experiment,source_digest
from supermercado.randomness import generate_day
from .helpers import model


class ExperimentTests(unittest.TestCase):
    def small(self):
        return model(end=20,bands=(Band('dia',0,20,.4,2),),scan_minutes=.05)

    def test_comparison_holds_staff_and_clients_controls(self):
        c=self.small()
        cases=variants(c,'comparacion')
        self.assertEqual(len(cases),6)
        self.assertTrue(all(x.cashiers == c.cashiers for x in cases.values()))
        self.assertTrue(all(x.priority_fraction == c.priority_fraction for x in cases.values()))

    def test_capacity_search_respects_five_physical_boxes(self):
        c=Config.load('ejemplos/base.json')
        cases=variants(c,'capacidad')
        self.assertEqual(len(cases),125)
        self.assertTrue(all(1 <= b.boxes <= 5 for c in cases.values() for b in c.bands))

    def test_queue_comparison_keeps_inputs_and_pairs_matching_policies(self):
        c=replace(self.small(),queue_mode='individuales',switch_threshold=2)
        cases=variants(c,'filas')
        self.assertEqual(len(cases),12)
        for name,individual in cases.items():
            if not name.endswith('_individuales'):
                continue
            unique=cases[name.removesuffix('_individuales')+'_unica']
            self.assertEqual(individual.cashiers,unique.cashiers)
            self.assertEqual(individual.bands,unique.bands)
            self.assertEqual(individual.mode,unique.mode)
            self.assertIsNone(individual.switch_threshold)
            self.assertIsNone(unique.switch_threshold)
            self.assertEqual(generate_day(individual,123,0),generate_day(unique,123,0))
        with tempfile.TemporaryDirectory() as temp:
            run_experiment(c,'filas',2,123,temp)
            pairs=json.loads((Path(temp)/'comparaciones_pareadas.json').read_text())
            for name,pair in pairs.items():
                self.assertEqual(pair['reference'],name.rsplit('_',1)[0]+'_unica')
                self.assertEqual(pair['n']+len(pair['excluded_seeds']),2)

    def test_factorial_has_27_combinations(self):
        self.assertEqual(len(variants(self.small(),'factorial')),27)

    def test_sensitivity_limit_varies_on_quick_policy(self):
        cases=variants(self.small(),'sensibilidad')
        self.assertEqual(cases['limite_rapida_5'].mode,'rapida_exclusiva')
        self.assertEqual(cases['demanda_alta'].demand_multiplier,1.2)

    def test_staff_adjustment_is_explicit(self):
        c=self.small()
        cases=variants(c,'comparacion',adjust_staff=True)
        self.assertEqual(len(cases['referencia_normal'].cashiers),2)
        self.assertEqual(len(cases['cinco_todas_franjas_normal'].cashiers),5)
        self.assertTrue(all(not w.breaks for c in cases.values() for w in c.cashiers))

    def test_stress_absence_is_only_for_selected_day(self):
        c=Config.load('ejemplos/base.json')
        cases=variants(c,'estres')
        workers=cases['ausencia_manana_promocion'].cashiers
        absences=[a for w in workers for a in w.absences]
        self.assertEqual(absences,[(2,0,300)])

    def test_single_run_exports_readable_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            summary=run_once(self.small(),123,temp)
            files={p.name for p in Path(temp).iterdir()}
            self.assertTrue({'manifest.json','resumen.json','verificacion.json','clientes.csv','eventos.csv','intervalos.csv','cohortes.csv','recursos.csv','dias.csv'} <= files)
            self.assertTrue(json.loads((Path(temp)/'verificacion.json').read_text())['ok'])
            self.assertEqual(summary['estado'],'completo')
            self.assertEqual(json.loads((Path(temp)/'manifest.json').read_text())['seeds'],[123])

    def test_paired_experiment_and_conservative_recommendation(self):
        with tempfile.TemporaryDirectory() as temp:
            stats,recommendation=run_experiment(self.small(),'comparacion',3,123,temp,target_success=.99)
            self.assertEqual(len(stats),6)
            self.assertIsNone(recommendation['selected'])
            pairs=json.loads((Path(temp)/'comparaciones_pareadas.json').read_text())
            self.assertTrue(all(x['reference'] == 'referencia_normal' for x in pairs.values()))
            self.assertEqual(pairs['referencia_normal']['mean'],0)
            self.assertTrue((Path(temp)/'replicas.csv').exists())

    def test_missing_target_does_not_invent_winner(self):
        with tempfile.TemporaryDirectory() as temp:
            stats,recommendation=run_experiment(self.small(),'comparacion',2,123,temp)
            self.assertIsNone(recommendation['selected'])
            self.assertIn('Falta acordar',recommendation['reason'])

    def test_invalid_experiment_arguments(self):
        with tempfile.TemporaryDirectory() as temp:
            for kwargs in ({'replicas':1},{'replicas':2,'confidence':1},{'replicas':2,'target_success':0}):
                with self.assertRaises(ValueError):
                    run_experiment(self.small(),'comparacion',seed=1,output=temp,**kwargs)

    def test_manifest_source_digest_has_sha256_length(self):
        self.assertEqual(len(source_digest()),64)
        self.assertEqual(source_digest(),source_digest())

    def test_cli_can_override_pending_priority(self):
        with tempfile.TemporaryDirectory() as temp:
            data=self.small().to_dict()
            data['priority_fraction']=None
            path=Path(temp)/'config.json'
            path.write_text(json.dumps(data))
            with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
                status=main(['simular','--config',str(path),'--salida',str(Path(temp)/'salida'),'--prioritarios','.2','--sin-traza'])
            self.assertEqual(status,0)
            self.assertFalse((Path(temp)/'salida/eventos.csv').exists())

    def test_cli_missing_file_has_clear_nonzero_exit(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()) as errors:
            status=main(['simular','--config','/no/existe/config.json','--salida','/no/usado'])
        self.assertEqual(status,2)
        self.assertIn('Error:',errors.getvalue())

    def test_infeasible_replicas_excluded_from_wait_inference_not_success_rate(self):
        c=model(end=20,bands=(Band('dia',0,20,1,1),),products_min=40,products_max=40)
        with tempfile.TemporaryDirectory() as temp:
            stats,_=run_experiment(c,'comparacion',2,123,temp)
            exclusive=stats['referencia_rapida_exclusiva']
            self.assertEqual(exclusive['semanas_inviables'],2)
            self.assertEqual(exclusive['max_p95_franja']['n'],0)
            self.assertEqual(exclusive['cumplimiento_semanal']['n'],2)
            self.assertEqual(exclusive['cumplimiento_semanal']['probability'],0)
            pairs=json.loads((Path(temp)/'comparaciones_pareadas.json').read_text())
            self.assertEqual(len(pairs['referencia_rapida_exclusiva']['excluded_seeds']),2)
