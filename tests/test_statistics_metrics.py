import copy
from dataclasses import replace
import math
import unittest
from supermercado.config import Band
from supermercado.domain import WeekResult
from supermercado.engine import simulate_day
from supermercado.metrics import cohort_rows,resource_rows,week_metrics,recovery_time
from supermercado.statistics import percentile,student_quantile,mean_interval,wilson_interval,paired_interval
from supermercado.validation import verify_day
from .helpers import model,client


class StatisticsTests(unittest.TestCase):
    def test_percentile_known_linear_interpolation(self):
        self.assertEqual(percentile([0,10],95),9.5)
        self.assertEqual(percentile([4,1,2,3],50),2.5)
        self.assertEqual(percentile([7],99),7)
        self.assertIsNone(percentile([],95))

    def test_student_known_quantiles(self):
        # Valores tabulados; se comprueba también df=1, donde la normal falla.
        for p,df,expected in ((.95,1,6.313751515),(.975,1,12.706204736),
                              (.95,10,1.812461123),(.95,29,1.699127027)):
            with self.subTest(df=df,p=p):
                self.assertAlmostEqual(student_quantile(p,df),expected,places=7)
        self.assertEqual(student_quantile(.5,10),0)
        self.assertAlmostEqual(student_quantile(.05,10),-1.812461123,places=7)

    def test_mean_interval_known_case(self):
        r=mean_interval([1,2,3],.9)
        self.assertEqual(r['mean'],2)
        self.assertEqual(r['sd'],1)
        self.assertAlmostEqual(r['half_width'],1.685854461,places=7)

    def test_insufficient_samples_have_no_interval(self):
        for values in ([],[2]):
            self.assertIsNone(mean_interval(values)['lower'])
        self.assertIsNone(mean_interval([])['mean'])

    def test_constant_sample(self):
        r=mean_interval([3]*30)
        self.assertEqual((r['lower'],r['upper'],r['half_width']),(3,3,0))

    def test_wilson_all_successes_not_certainty(self):
        r=wilson_interval(30,30,.9)
        self.assertAlmostEqual(r['lower'],.91727569,places=6)
        self.assertEqual(r['probability'],1)
        self.assertAlmostEqual(r['upper'],1)
        self.assertIsNone(wilson_interval(0,0)['probability'])

    def test_wilson_no_successes(self):
        r=wilson_interval(0,30,.9)
        self.assertAlmostEqual(r['lower'],0)
        self.assertGreater(r['upper'],0)

    def test_paired_by_seed_not_order(self):
        r=paired_interval({1:10,2:20,3:30},{3:27,1:7,2:17})
        self.assertEqual((r['mean'],r['sd']),(-3,0))

    def test_invalid_statistics(self):
        for action in (lambda: percentile([1],101),lambda: student_quantile(1,2),
                       lambda: student_quantile(.9,0),lambda: mean_interval([math.nan]),
                       lambda: mean_interval([1,2],1),lambda: wilson_interval(2,1),
                       lambda: paired_interval({1:2},{2:2})):
            with self.assertRaises(ValueError):
                action()


class MetricsTests(unittest.TestCase):
    def test_wait_percentile_is_not_total_percentile(self):
        c=model()
        day=simulate_day(c,[client(0),client(1,1)])
        row=cohort_rows(day,c,groups=False)[0]
        self.assertAlmostEqual(row['p95_espera'],1.425)
        self.assertAlmostEqual(row['p95_total'],3.925)

    def test_time_weighted_queue_and_utilization(self):
        c=model(end=10)
        day=simulate_day(c,[client(0),client(1,1)])
        row=resource_rows(day)[0]
        self.assertAlmostEqual(row['cola_media'],.15)
        self.assertAlmostEqual(row['utilizacion'],.5)
        self.assertEqual(row['throughput_hora'],12)

    def test_empty_cohort_is_not_zero_wait_evidence(self):
        c=model()
        day=simulate_day(c,[])
        row=cohort_rows(day,c,False)[0]
        self.assertIsNone(row['p95_espera'])
        self.assertIsNone(row['cumple_espera'])
        summary=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertIsNone(summary['cumple_servicio_semana'])

    def test_arrival_cohort_kept_across_band_boundary(self):
        c=model(bands=(Band('a',0,2,0,1),Band('b',2,10,0,1)))
        day=simulate_day(c,[client(0,1,40),client(1,1.5)])
        rows=cohort_rows(day,c,False)
        self.assertEqual([r['llegados'] for r in rows],[2,0])
        self.assertGreater(day.records[1].start,2)

    def test_abandonment_cannot_improve_service_success(self):
        c=model()
        day=simulate_day(c,[client(0,products=40),client(1,1,patience=1)])
        m=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertTrue(m['cumple_espera_semana'])
        self.assertFalse(m['cumple_servicio_semana'])
        self.assertEqual(m['abandonos'],1)

    def test_payment_failure_is_reported_separately(self):
        c=model(rejection_probability=1)
        day=simulate_day(c,[client(0)])
        m=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertEqual(m['pagos_fallidos'],1)
        self.assertEqual(m['atendidos'],0)
        self.assertFalse(m['cumple_servicio_semana'])

    def test_paid_staff_and_enabled_boxes_differ(self):
        c=model(end=10,hourly_wage=60)
        day=simulate_day(c,[])
        m=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertAlmostEqual(m['horas_cajero'],50/60)
        self.assertAlmostEqual(m['horas_caja'],10/60)
        self.assertEqual(m['costo_personal'],50)

    def test_overtime_cost_and_resource_accounting(self):
        c=model(end=10,hourly_wage=60,overtime_wage_multiplier=2)
        day=simulate_day(c,[client(0,9,40)])
        m=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertEqual(m['costo_personal'],62)
        self.assertEqual(m['horas_cajero_extra'],.1)
        self.assertEqual(m['max_minutos_extra'],6)

    def test_overtime_includes_shift_handover_before_commercial_closing(self):
        from supermercado.config import Cashier
        c=model(end=20,cashiers=(Cashier('old',0,2),Cashier('new',2,20)))
        day=simulate_day(c,[client(0,products=40)])
        m=week_metrics(WeekResult([day],1,'completo'),c)
        self.assertEqual(m['horas_cajero_extra'],5/60)
        self.assertEqual(m['horas_cajero_post_cierre'],0)

    def test_recovery_requires_sustained_observation(self):
        c=model(end=15)
        day=simulate_day(c,[client(0,products=40),client(1,1)])
        self.assertEqual(recovery_time(day,3,0,2),4)
        self.assertIsNone(recovery_time(day,3,0,20))
        with self.assertRaises(ValueError):
            recovery_time(simulate_day(c,[],trace=False),0)

    def test_conservation_checker_catches_area_corruption(self):
        c=model()
        day=simulate_day(c,[client(0),client(1,1)])
        day.resources['dia']['queue_area']=0
        self.assertTrue(any('Área de cola' in e for e in verify_day(day,c)))

    def test_week_with_any_bad_band_fails_joint_target(self):
        c=model(sla_minutes=1)
        day=simulate_day(c,[client(0,products=40),client(1,1)])
        self.assertFalse(week_metrics(WeekResult([day],1,'completo'),c)['cumple_espera_semana'])

    def test_infeasible_week_not_treated_as_complete_wait_distribution(self):
        c=model(mode='rapida_exclusiva')
        day=simulate_day(c,[client(0,products=40),client(1,products=5)])
        m=week_metrics(WeekResult([day],1,'inviable'),c)
        self.assertIsNone(m['max_p95_franja'])
        self.assertIsNone(m['espera_media'])
        self.assertIsNotNone(m['max_p95_observado'])
        self.assertFalse(m['cumple_servicio_semana'])
