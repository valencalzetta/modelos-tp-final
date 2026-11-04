import copy
from dataclasses import replace
import random
import unittest
from supermercado.config import Band, Cashier
from supermercado.engine import simulate_day, simulate_week
from supermercado.validation import verify_day
from .helpers import model,client


class EngineTests(unittest.TestCase):
    def checked(self,c,customers):
        r=simulate_day(c,customers)
        self.assertEqual(verify_day(r,c),[])
        return r

    def test_manual_two_customers(self):
        r=self.checked(model(),[client('a'),client('b',1)])
        self.assertEqual([(x.start,x.finish,x.wait) for x in r.records],[(0,2.5,0),(2.5,5,1.5)])

    def test_analytic_dd1(self):
        customers=[client(i,i*2) for i in range(15)]
        r=self.checked(model(),customers)
        self.assertEqual([x.wait for x in r.records],[i*.5 for i in range(15)])

    def test_simultaneous_arrivals_fifo_input_order(self):
        r=self.checked(model(),[client(9),client(3),client(1)])
        self.assertEqual([x.start for x in r.records],[0,2.5,5])

    def test_unsorted_input(self):
        r=self.checked(model(),[client('late',5),client('early',0)])
        self.assertEqual([x.customer.id for x in r.records],['early','late'])

    def test_completion_arrival_same_instant(self):
        r=self.checked(model(),[client(0),client(1,2.5)])
        self.assertEqual([x.wait for x in r.records],[0,0])

    def test_priority_without_preemption(self):
        r=self.checked(model(),[client(0,0,20),client(1,1),client(2,2,priority=True)])
        byid={x.customer.id:x for x in r.records}
        self.assertEqual(byid['0'].finish,4)
        self.assertEqual(byid['2'].start,4)
        self.assertEqual(byid['1'].start,6.5)

    def test_fifo_within_priority(self):
        r=self.checked(model(),[client(0,0,20),client(1,1,priority=True),client(2,2,priority=True)])
        self.assertLess(r.records[1].start,r.records[2].start)

    def test_two_boxes_parallel(self):
        r=self.checked(model(boxes=2),[client(0),client(1),client(2,1)])
        self.assertEqual([x.start for x in r.records],[0,0,2.5])

    def test_idle_period_not_erased(self):
        r=self.checked(model(end=20),[client(0,10)])
        self.assertEqual(r.records[0].start,10)
        self.assertEqual(r.resources['dia']['enabled_minutes'],20)

    def test_empty_day_retains_scheduled_horizon(self):
        r=self.checked(model(),[])
        self.assertEqual((r.status,r.finish),('completo',30))
        self.assertEqual(r.resources['dia']['staff_minutes'],150)

    def test_capacity_increase_preserves_waiting(self):
        c=model(bands=(Band('a',0,5,0,1),Band('b',5,20,0,2)),cashiers=(Cashier('a',0,20),Cashier('b',0,20)))
        r=self.checked(c,[client(0,0,40),client(1,1)])
        self.assertEqual(r.records[1].start,5)
        self.assertEqual(r.records[1].box,2)
        self.assertEqual(r.records[1].band,'a')

    def test_capacity_decrease_does_not_interrupt(self):
        c=model(bands=(Band('a',0,1,0,2),Band('b',1,20,0,1)),cashiers=(Cashier('a',0,20),Cashier('b',0,20)))
        r=self.checked(c,[client(0,0,40),client(1,0),client(2,1.1)])
        self.assertEqual(r.records[1].finish,2.5)
        self.assertEqual(r.records[2].start,7)
        self.assertEqual(r.records[2].box,1)

    def test_insufficient_staff_limits_open_boxes(self):
        c=model(boxes=5,cashiers=(Cashier('only',0,30),))
        r=self.checked(c,[client(i) for i in range(4)])
        self.assertTrue(all(x.box == 1 for x in r.records))
        self.assertTrue(all(i['enabled'] <= 1 for i in r.intervals))

    def test_shift_handover_waits_until_completion(self):
        c=model(end=20,cashiers=(Cashier('old',0,2),Cashier('new',2,20)))
        r=self.checked(c,[client(0,0,40),client(1,1)])
        self.assertEqual([(x.start,x.cashier) for x in r.records],[(0,'old'),(7,'new')])
        self.assertEqual(r.cashier_minutes['old'],7)

    def test_break_during_idle_time(self):
        c=model(cashiers=(Cashier('a',0,30,breaks=((1,3),)),))
        r=self.checked(c,[client(0,2)])
        self.assertEqual(r.records[0].start,4)

    def test_break_postponed_in_full_until_service_finishes(self):
        c=model(cashiers=(Cashier('a',0,30,breaks=((1,3),)),))
        r=self.checked(c,[client(0),client(1,1)])
        self.assertEqual(r.records[1].start,5.5)
        self.assertTrue(any(e['kind'] == 'pausa_diferida' for e in r.events))

    def test_absence_before_arrival(self):
        c=model(cashiers=(Cashier('a',0,30,absences=((0,0,5),)),))
        r=self.checked(c,[client(0,1)])
        self.assertEqual(r.records[0].start,5)

    def test_absence_does_not_preempt(self):
        c=model(cashiers=(Cashier('a',0,30,absences=((0,1,5),)),))
        r=self.checked(c,[client(0),client(1,1)])
        self.assertEqual(r.records[0].finish,2.5)
        self.assertEqual(r.records[1].start,5)

    def test_different_cashier_speeds_affect_scan_only(self):
        c=model(boxes=2,cashiers=(Cashier('a',0,30,speed=2),Cashier('b',0,30,speed=1)))
        r=self.checked(c,[client(0),client(1)])
        self.assertEqual([x.finish for x in r.records],[4,2.5])

    def test_cash_payment_one_minute_longer(self):
        c=model(boxes=2)
        r=self.checked(c,[client(0),client(1,payment='efectivo')])
        self.assertEqual(r.records[1].finish-r.records[0].finish,1)

    def test_exclusive_quick_rejects_large_baskets(self):
        c=model(boxes=2,mode='rapida_exclusiva')
        r=self.checked(c,[client(0,products=40),client(1,products=5)])
        self.assertEqual([x.box for x in r.records],[2,1])
        self.assertFalse(any(x.flexible_exception for x in r.records))

    def test_small_basket_can_use_normal_box(self):
        c=model(boxes=2,mode='rapida_exclusiva')
        r=self.checked(c,[client(0,products=5),client(1,products=5)])
        self.assertEqual([x.box for x in r.records],[1,2])

    def test_flexible_quick_can_take_large_basket(self):
        c=model(boxes=2,mode='rapida_flexible')
        r=self.checked(c,[client(0,products=40),client(1,products=40)])
        self.assertTrue(r.records[0].flexible_exception)
        self.assertEqual([x.start for x in r.records],[0,0])

    def test_flexible_quick_prefers_eligible_customers(self):
        c=model(boxes=2,mode='rapida_flexible')
        r=self.checked(c,[client(0,products=40,priority=True),client(1,products=5)])
        self.assertEqual([x.box for x in r.records],[2,1])

    def test_exclusive_quick_only_is_reported_infeasible(self):
        c=model(mode='rapida_exclusiva')
        r=self.checked(c,[client(0,products=40)])
        self.assertEqual(r.status,'inviable')
        self.assertIsNone(r.records[0].start)
        self.assertIn('capacidad',r.note)

    def test_individual_queues_route_to_shortest(self):
        c=model(boxes=2,queue_mode='individuales')
        r=self.checked(c,[client(i) for i in range(3)])
        self.assertEqual([x.box for x in r.records],[1,2,1])

    def test_individual_queue_closure_transfers_customers(self):
        c=model(queue_mode='individuales',bands=(Band('a',0,1,0,2),Band('b',1,30,0,1)),cashiers=(Cashier('a',0,30),Cashier('b',0,30)))
        r=self.checked(c,[client(i,0,40) for i in range(5)])
        self.assertGreater(sum(x.queue_changes for x in r.records),0)
        self.assertEqual(sum(x.status == 'atendido' for x in r.records),5)

    def test_reactive_opening_respects_delay(self):
        c=model(reactive_threshold=2,reactive_delay=1,reactive_min_open=5)
        r=self.checked(c,[client(i,0,40) for i in range(4)])
        self.assertEqual(r.records[1].start,1)
        self.assertEqual(r.records[1].box,2)
        self.assertTrue(all(i['enabled'] <= 2 for i in r.intervals))

    def test_reactive_opening_cannot_create_staff(self):
        c=model(reactive_threshold=1,reactive_delay=1,cashiers=(Cashier('a',0,30),))
        r=self.checked(c,[client(i,0,40) for i in range(3)])
        self.assertTrue(all(i['enabled'] <= 1 for i in r.intervals))

    def test_payment_retry_holds_box(self):
        c=model(scan_minutes=0,rejection_probability=.5,max_payment_attempts=2,retry_delay=2)
        r=self.checked(c,[client(0,payment_draws=(.1,.9)),client(1,1)])
        first=r.records[0]
        self.assertEqual((first.finish,first.attempts,first.rejections),(4,2,1))
        self.assertEqual(r.records[1].start,4)

    def test_payment_exhaustion_falls_back_to_cash(self):
        c=model(scan_minutes=0,rejection_probability=1,max_payment_attempts=2,retry_delay=1,payment_exhaustion='efectivo')
        r=self.checked(c,[client(0,payment_draws=(0,0))])
        x=r.records[0]
        self.assertEqual((x.finish,x.attempts,x.rejections,x.fallback_cash),(5,3,2,True))
        self.assertEqual(x.status,'atendido')

    def test_payment_exhaustion_can_fail_sale(self):
        c=model(scan_minutes=0,rejection_probability=1)
        r=self.checked(c,[client(0,payment_draws=(0,))])
        self.assertEqual(r.records[0].status,'pago_fallido')
        self.assertEqual(r.status,'completo')

    def test_cash_never_has_digital_rejection(self):
        c=model(scan_minutes=0,rejection_probability=1)
        r=self.checked(c,[client(0,payment='efectivo')])
        self.assertEqual((r.records[0].finish,r.records[0].rejections),(2,0))

    def test_abandonment_removes_only_waiting_customer(self):
        r=self.checked(model(),[client(0,products=40),client(1,1,patience=2)])
        self.assertEqual(r.records[1].status,'abandono')
        self.assertEqual(r.records[1].exit_time,3)
        self.assertEqual(r.resources['dia']['queue_area'],2)

    def test_abandonment_tie_serves_customer(self):
        r=self.checked(model(),[client(0),client(1,0,patience=2.5)])
        self.assertEqual(r.records[1].start,2.5)
        self.assertEqual(r.records[1].status,'atendido')

    def test_zero_patience_can_start_immediately(self):
        r=self.checked(model(),[client(0,patience=0)])
        self.assertEqual(r.records[0].status,'atendido')

    def test_closing_does_not_discard_client(self):
        c=model(end=10)
        r=self.checked(c,[client(0,9,40)])
        self.assertEqual((r.finish,r.pending_at_close),(16,1))
        self.assertEqual(r.resources['fuera_horario']['staff_minutes'],6)
        self.assertEqual(r.resources['fuera_horario']['busy_minutes'],6)

    def test_no_future_staff_reports_pending(self):
        c=model(cashiers=(Cashier('a',0,30,days=(1,)),))
        r=self.checked(c,[client(0)])
        self.assertEqual(r.status,'inviable')
        self.assertEqual(r.records[0].status,'pendiente')

    def test_next_opening_is_hard_boundary_without_reset(self):
        c=model(scan_minutes=100)
        r=self.checked(c,[client(0,products=40)])
        self.assertEqual(r.status,'inviable')
        self.assertEqual(r.finish,1440)
        self.assertIn('apertura siguiente',r.note)

    def test_week_stops_after_infeasible_day(self):
        c=replace(model(mode='rapida_exclusiva'),days=2)
        week=simulate_week(c,inputs={0:[client(0,products=40)],1:[]})
        self.assertEqual((week.status,len(week.days)),('inviable',1))

    def test_input_is_not_mutated(self):
        customers=[client(0),client(1,1)]
        before=copy.deepcopy(customers)
        self.checked(model(),customers)
        self.assertEqual(before,customers)

    def test_reproducibility(self):
        c=model(scan_minutes=0,rejection_probability=.6,max_payment_attempts=3,retry_delay=1)
        customers=[client(i,i*.5) for i in range(10)]
        self.assertEqual(simulate_day(c,customers,seed=81),simulate_day(c,customers,seed=81))

    def test_randomized_invariants_for_all_policies(self):
        for seed in range(8):
            rng=random.Random(seed)
            for mode in ('normal','rapida_exclusiva','rapida_flexible'):
                for queue in ('unica','individuales'):
                    with self.subTest(seed=seed,mode=mode,queue=queue):
                        c=model(boxes=3,mode=mode,queue_mode=queue,rejection_probability=.2,
                                max_payment_attempts=2,retry_delay=.2,payment_exhaustion='efectivo',
                                switch_threshold=2 if queue == 'individuales' else None)
                        customers=[client(i,rng.uniform(0,29),rng.randint(1,40),priority=rng.random()<.2,
                                          patience=rng.choice([None,3,10])) for i in range(40)]
                        self.checked(c,customers)

    def test_more_boxes_cannot_delay_fixed_fifo_workload(self):
        customers=[client(i,i*.7,(i*7)%40+1) for i in range(30)]
        one=self.checked(model(),customers)
        five=self.checked(model(boxes=5),customers)
        self.assertTrue(all(b.start <= a.start for a,b in zip(one.records,five.records)))

    def test_corrupted_trace_detected(self):
        c=model()
        r=self.checked(c,[client(0),client(1,1)])
        r.records[1].start=1
        self.assertTrue(any('Superposición' in e for e in verify_day(r,c)))

    def test_invalid_customer_rejected(self):
        for customer in (client(0,-1),client(0,30),client(0,products=0),client(0,payment='otro'),client(0,patience=-1)):
            with self.subTest(customer=customer),self.assertRaises(ValueError):
                simulate_day(model(),[customer])

    def test_duplicate_customer_rejected(self):
        with self.assertRaises(ValueError):
            simulate_day(model(),[client(0),client(0,1)])

    def test_wrong_customer_day_rejected(self):
        with self.assertRaises(ValueError):
            simulate_day(model(),[client(0,day=1)])

    def test_completion_at_closing_not_counted_as_pending(self):
        c=model(end=10)
        r=self.checked(c,[client(0,7.5)])
        self.assertEqual(r.records[0].finish,10)
        self.assertEqual(r.pending_at_close,0)

    def test_invalid_customer_numeric_types(self):
        for customer in (client(0,arrival="1"),client(0,patience="2"),client(0,payment_draws=(1,))):
            with self.subTest(customer=customer),self.assertRaises(ValueError):
                simulate_day(model(),[customer])
