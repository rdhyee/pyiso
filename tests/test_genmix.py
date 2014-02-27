from apps.clients import client_factory
from django.test import TestCase
from apps.gridentities.models import FuelType, BalancingAuthority
from apps.griddata.models import DataPoint
import pytz
from datetime import datetime, timedelta

class TestGenMix(TestCase):
    fixtures = ['isos.json', 'gentypes.json']
    
    def _run_test(self, ba_name, **kwargs):
        # get data
        c = client_factory(ba_name)
        data = c.get_generation(**kwargs)
        
        # test number
        self.assertGreater(len(data), 1)
                
        # test contents
        for dp in data:
            # test key names
            self.assertEqual(set(['gen_MW', 'ba_name', 'fuel_name',
                                  'timestamp', 'freq', 'market']),
                             set(dp.keys()))
    
            # test values
            self.assertEqual(dp['timestamp'].tzinfo, pytz.utc)
            self.assertEqual(FuelType.objects.filter(name=dp['fuel_name']).count(), 1)
            self.assertEqual(BalancingAuthority.objects.filter(abbrev=dp['ba_name']).count(), 1)
            
            # test for numeric gen
            self.assertGreaterEqual(dp['gen_MW']+1, dp['gen_MW'])
            
        # return
        return data
        
    def test_isne_latest(self):
        # basic test
        data = self._run_test('ISONE', latest=True)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
                
    def test_isne_date_range(self):
        # basic test
        data = self._run_test('ISONE', start_at=datetime.today()-timedelta(days=2),
                              end_at=datetime.today()-timedelta(days=1))
        
        # test multiple
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_miso_latest(self):
        # basic test
        data = self._run_test('MISO', latest=True)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
                
    def test_spp_latest_hr(self):
        # basic test
        data = self._run_test('SPP', latest=True, market=DataPoint.RTHR)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RTHR)
            self.assertEqual(dp['freq'], DataPoint.HOURLY)                
        
    def test_spp_date_range_hr(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('SPP', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1),
                                market=DataPoint.RTHR)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RTHR)
            self.assertEqual(dp['freq'], DataPoint.HOURLY)                
        
    def test_spp_latest_5min(self):
        # basic test
        data = self._run_test('SPP', latest=True, market=DataPoint.RT5M)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RT5M)
            self.assertEqual(dp['freq'], DataPoint.FIVEMIN)                
        
    def test_spp_yesterday_5min(self):
        # basic test
        data = self._run_test('SPP', yesterday=True, market=DataPoint.RT5M)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RT5M)
            self.assertEqual(dp['freq'], DataPoint.FIVEMIN)                

    def test_bpa_latest(self):
        # basic test
        data = self._run_test('BPA', latest=True, market=DataPoint.RT5M)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RT5M)
            self.assertEqual(dp['freq'], DataPoint.FIVEMIN)                

    def test_bpa_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('BPA', start_at=today-timedelta(days=2),
                              end_at=today-timedelta(days=1))
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)

    def test_bpa_date_range_farpast(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('BPA', start_at=today-timedelta(days=20),
                              end_at=today-timedelta(days=10))
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)
        
    def test_caiso_date_range(self):
        # basic test
        today = datetime.today().replace(tzinfo=pytz.utc)
        data = self._run_test('CAISO', start_at=today-timedelta(days=3),
                              end_at=today-timedelta(days=2), market=DataPoint.RTHR)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RTHR)
            self.assertEqual(dp['freq'], DataPoint.HOURLY)                

        # test fuel names
        fuels = set([d['fuel_name'] for d in data])
        expected_fuels = ['solarpv', 'solarth', 'geo', 'smhydro', 'wind', 'biomass', 'biogas',
                          'thermal', 'hydro', 'nuclear']
        for expfuel in expected_fuels:
            self.assertIn(expfuel, fuels)

    def test_caiso_yesterday(self):
        # basic test
        data = self._run_test('CAISO', yesterday=True, market=DataPoint.RTHR)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertGreater(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RTHR)
            self.assertEqual(dp['freq'], DataPoint.HOURLY)                

        # test fuel names
        fuels = set([d['fuel_name'] for d in data])
        expected_fuels = ['solarpv', 'solarth', 'geo', 'smhydro', 'wind', 'biomass', 'biogas',
                          'thermal', 'hydro', 'nuclear']
        for expfuel in expected_fuels:
            self.assertIn(expfuel, fuels)

    def test_caiso_latest(self):
        # basic test
        data = self._run_test('CAISO', latest=True)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RT5M)
            self.assertEqual(dp['freq'], DataPoint.TENMIN)                

        # test fuel names
        fuels = set([d['fuel_name'] for d in data])
        expected_fuels = ['solar', 'wind', 'renewable', 'other']
        for expfuel in expected_fuels:
            self.assertIn(expfuel, fuels)

    def test_ercot_latest(self):
        # before min 32, will not have wind data
        if datetime.now().minute >= 32:
            # basic test
            data = self._run_test('ERCOT', latest=True)
            
            # test all timestamps are equal
            timestamps = [d['timestamp'] for d in data]
            self.assertEqual(len(set(timestamps)), 1)
            
            # test flags
            for dp in data:
                self.assertEqual(dp['market'], DataPoint.RTHR)
                self.assertEqual(dp['freq'], DataPoint.HOURLY)                
    
            # test fuel names
            fuels = set([d['fuel_name'] for d in data])
            expected_fuels = ['wind', 'nonwind']
            for expfuel in expected_fuels:
                self.assertIn(expfuel, fuels)
                
        else:
            c = client_factory('ERCOT')
            data = c.get_generation(latest=True)
            self.assertEqual(len(data), 0)
            
    def test_pjm_latest(self):
        # basic test
        data = self._run_test('PJM', latest=True)
        
        # test all timestamps are equal
        timestamps = [d['timestamp'] for d in data]
        self.assertEqual(len(set(timestamps)), 1)
        
        # test flags
        for dp in data:
            self.assertEqual(dp['market'], DataPoint.RT5M)
            self.assertEqual(dp['freq'], DataPoint.FIVEMIN)                

        # test fuel names
        fuels = set([d['fuel_name'] for d in data])
        expected_fuels = ['wind', 'nonwind']
        for expfuel in expected_fuels:
            self.assertIn(expfuel, fuels)
            