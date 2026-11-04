from dataclasses import replace
import json
import unittest
from supermercado.config import Config, Band, Cashier, with_capacity, roster_for_bands
from supermercado.randomness import generate_day, stable_seed
from .helpers import model


class ConfigTests(unittest.TestCase):
    def test_roundtrip_json(self):
        c=model(cashiers=(Cashier('a',0,30,breaks=((2,1),),absences=((0,4,5),)),))
        self.assertEqual(Config.from_dict(json.loads(json.dumps(c.to_dict()))),c)

    def test_priority_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,'priority_fraction'):
            replace(model(),priority_fraction=None).validate()

    def test_invalid_numeric_parameters(self):
        for key,value in [('days',0),('days',8),('installed_boxes',6),('scan_minutes',-1),
                          ('cash_fraction',1.1),('priority_fraction',-1),('quick_limit',0),
                          ('demand_multiplier',0),('retry_delay',-1),('hourly_wage',-1),
                          ('scan_minutes',float('nan')),('cash_fraction',True),
                          ('max_payment_attempts',0),('reactive_threshold',0),('switch_threshold',1)]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                replace(model(),**{key:value}).validate()

    def test_invalid_policies(self):
        for key in ('mode','queue_mode','payment_exhaustion'):
            with self.assertRaises(ValueError):
                replace(model(),**{key:'desconocido'}).validate()

    def test_bands_must_be_contiguous(self):
        with self.assertRaises(ValueError):
            model(bands=(Band('a',0,10,1,2),Band('b',11,30,1,2)))

    def test_no_more_than_five_open_boxes(self):
        with self.assertRaises(ValueError):
            model(bands=(Band('a',0,30,1,6),))

    def test_duplicate_cashiers_rejected(self):
        with self.assertRaises(ValueError):
            model(cashiers=(Cashier('a',0,30),Cashier('a',0,30)))

    def test_invalid_breaks_and_agenda(self):
        for c in (Cashier('a',0,30,breaks=((29,2),)),Cashier('a',0,30,breaks=((2,4),(3,2))),
                  Cashier('a',0,30,speed=0),Cashier('a',0,30,days=(0,0))):
            with self.subTest(c=c),self.assertRaises(ValueError):
                model(cashiers=(c,))

    def test_staff_must_be_explicit(self):
        with self.assertRaisesRegex(ValueError,'agenda'):
            model(cashiers=())

    def test_capacity_does_not_silently_change_roster(self):
        c=model()
        self.assertEqual(with_capacity(c,[3]).cashiers,c.cashiers)
        self.assertEqual(len(with_capacity(c,[3],True).cashiers),3)

    def test_example_configuration_loads(self):
        c=Config.load('ejemplos/base.json')
        self.assertEqual(c.installed_boxes,5)
        self.assertEqual(len(c.cashiers),10)
        self.assertIn('supuesto',c.assumptions['priority_fraction'])


class GenerationTests(unittest.TestCase):
    def config(self,**kwargs):
        return model(bands=(Band('a',0,10,1,2),Band('b',10,20,.5,2)),**kwargs)

    def test_generation_reproducible(self):
        c=self.config()
        self.assertEqual(generate_day(c,123,0),generate_day(c,123,0))

    def test_policy_does_not_change_clients(self):
        c=self.config()
        self.assertEqual(generate_day(c,12,0),generate_day(replace(c,mode='rapida_exclusiva'),12,0))

    def test_priority_change_preserves_other_attributes(self):
        c=self.config()
        a=generate_day(c,12,0)
        b=generate_day(replace(c,priority_fraction=1),12,0)
        self.assertTrue(all(not x.priority and y.priority for x,y in zip(a,b)))
        self.assertEqual([(x.arrival,x.products,x.payment) for x in a],[(x.arrival,x.products,x.payment) for x in b])

    def test_seeds_and_streams_differ(self):
        self.assertNotEqual(stable_seed(1,'a'),stable_seed(1,'b'))
        c=self.config()
        self.assertNotEqual(generate_day(c,1,0),generate_day(c,2,0))

    def test_zero_rate_band_has_no_arrivals(self):
        c=model(bands=(Band('a',0,10,0,1),Band('b',10,20,1,1)))
        customers=generate_day(c,1,0)
        self.assertTrue(customers)
        self.assertTrue(all(10 <= x.arrival < 20 for x in customers))

    def test_generated_products_are_integers_and_bounded(self):
        c=self.config()
        for seed in range(10):
            for customer in generate_day(c,seed,0):
                self.assertIs(type(customer.products),int)
                self.assertTrue(1 <= customer.products <= 40)

    def test_higher_cash_fraction_uses_same_uniform_draws(self):
        c=self.config()
        a=generate_day(c,4,0)
        b=generate_day(replace(c,cash_fraction=.9),4,0)
        self.assertTrue(all(x.payment != 'efectivo' or y.payment == 'efectivo' for x,y in zip(a,b)))

    def test_arrival_count_matches_rate_over_many_fixed_seeds(self):
        c=model(bands=(Band('dia',0,30,1,1),))
        count=sum(len(generate_day(c,s,0)) for s in range(100))
        self.assertTrue(2700 < count < 3300,count)

    def test_promotion_increases_arrival_intensity(self):
        c=model(days=3,bands=(Band('dia',0,30,1,1),),promotion_multiplier=2)
        counts=[sum(len(generate_day(c,s,day)) for s in range(50)) for day in (0,2)]
        self.assertGreater(counts[1],counts[0]*1.7)
        self.assertLess(counts[1],counts[0]*2.3)

    def test_invalid_day(self):
        with self.assertRaises(ValueError):
            generate_day(self.config(),1,3)
